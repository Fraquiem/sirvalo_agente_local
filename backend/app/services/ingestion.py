"""Document parsing, deterministic chunking and embedding orchestration."""
from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import PurePath

import httpx
from fastapi import HTTPException, status
from pypdf import PdfReader

from app.config import settings
from app.services.vectorstore import (
    create_or_update_document,
    mark_document_error,
    replace_chunks,
)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".csv"}
ALLOWED_MIME_TYPES = {
    "application/pdf", "text/plain", "text/markdown", "text/csv",
    "application/csv", "application/vnd.ms-excel", "text/x-markdown",
}

@dataclass(frozen=True)
class ParsedDocument:
    text: str
    metadata: dict

@dataclass(frozen=True)
class Chunk:
    index: int
    content: str
    metadata: dict


def validate_upload(filename: str | None, content_type: str | None, size: int) -> str:
    if not filename or filename != PurePath(filename).name or filename in {".", ".."}:
        raise HTTPException(status_code=422, detail="Unsafe or missing filename")
    if not content_type or content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported MIME type")
    suffix = PurePath(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported file extension")
    if size > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MiB limit")
    return suffix


def _decode(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("File is not valid UTF-8") from exc


def extract_text(data: bytes, suffix: str) -> ParsedDocument:
    if suffix == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:
            raise ValueError("Unreadable PDF") from exc
        text = "\n\n".join(pages)
        metadata = {"format": "pdf", "pages": len(pages)}
    elif suffix == ".csv":
        try:
            rows = csv.reader(io.StringIO(_decode(data)))
            text = "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
        except (csv.Error, ValueError) as exc:
            raise ValueError("Unreadable CSV") from exc
        metadata = {"format": "csv"}
    else:
        text = _decode(data)
        metadata = {"format": "markdown" if suffix in {".md", ".markdown"} else "txt"}
    text = normalize_text(text)
    if not text:
        raise ValueError("File contains no readable text")
    return ParsedDocument(text=text, metadata=metadata)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def chunk_text(text: str, *, size: int | None = None, overlap: int | None = None) -> list[Chunk]:
    size = size or settings.CHUNK_SIZE
    overlap = overlap if overlap is not None else settings.CHUNK_OVERLAP
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Invalid chunk size or overlap")
    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind("\n", start + size // 2, end)
            if boundary > start:
                end = boundary
        content = text[start:end].strip()
        if content:
            chunks.append(Chunk(index=index, content=content, metadata={"start": start, "end": end}))
            index += 1
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


async def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    if not chunks:
        return []
    async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/embed",
            json={"model": settings.OLLAMA_EMBEDDING_MODEL, "input": [chunk.content for chunk in chunks]},
        )
    if response.status_code >= 400:
        raise RuntimeError("Embedding provider rejected the request")
    payload = response.json()
    embeddings = payload.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(chunks):
        raise RuntimeError("Embedding provider returned an invalid response")
    if any(not isinstance(vector, list) or len(vector) != settings.EMBEDDING_DIMENSIONS for vector in embeddings):
        raise RuntimeError("Embedding dimension does not match configured pgvector dimension")
    return embeddings


async def process_upload(*, data: bytes, filename: str, mime_type: str | None, user_id: str) -> dict:
    suffix = validate_upload(filename, mime_type, len(data))
    checksum = hashlib.sha256(data).hexdigest()
    parsed = extract_text(data, suffix)
    chunks = chunk_text(parsed.text)
    title = filename.rsplit(".", 1)[0]
    document = await create_or_update_document(
        owner_id=user_id, source_type="upload", source_uri=None,
        external_id=None, filename=filename, mime_type=mime_type,
        size_bytes=len(data), title=title, checksum=checksum,
        metadata={**parsed.metadata, "chunk_size": settings.CHUNK_SIZE, "chunk_overlap": settings.CHUNK_OVERLAP},
    )
    document_id = document["id"]
    try:
        embeddings = await embed_chunks(chunks)
        rows = [
            {"document_id": document_id, "chunk_index": chunk.index, "content": f"Title: {title}\nSource: {filename}\n\n{chunk.content}", "embedding": embedding, "metadata": {**chunk.metadata, "source_type": "upload", "filename": filename, "checksum": checksum}}
            for chunk, embedding in zip(chunks, embeddings)
        ]
        return await replace_chunks(document_id, rows)
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        await mark_document_error(document_id, str(exc))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Document processing provider unavailable") from exc


def file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
