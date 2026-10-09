from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import AuthenticatedUser, current_user
from app.services.cocktaildb import ingest_cocktails
from app.services.ingestion import process_upload
from app.services.vectorstore import delete_document, get_document, list_documents

router = APIRouter(tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    title: str | None = None
    filename: str | None = None
    source_type: str
    source_uri: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentsResponse(BaseModel):
    items: list[dict[str, Any]]


class CocktailIngestRequest(BaseModel):
    letters: list[str] = Field(default_factory=lambda: ["a"], min_length=1, max_length=26)
    limit: int = Field(default=20, ge=1, le=100)


@router.post("/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(file: UploadFile = File(...), user: AuthenticatedUser = Depends(current_user)) -> dict[str, Any]:
    data = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MiB limit")
    try:
        document = await process_upload(data=data, filename=file.filename or "", mime_type=file.content_type, user_id=user.id)
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Document store unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="File could not be processed") from exc
    return {"document": document}


@router.get("/documents")
async def get_documents(user: AuthenticatedUser = Depends(current_user)) -> DocumentsResponse:
    try:
        return DocumentsResponse(items=await list_documents(token=user.access_token))
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Document store unavailable") from exc


@router.get("/documents/{document_id}")
async def get_document_by_id(document_id: UUID, user: AuthenticatedUser = Depends(current_user)) -> dict[str, Any]:
    try:
        document = await get_document(document_id=str(document_id), token=user.access_token)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Document store unavailable") from exc
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document": document}


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(document_id: UUID, user: AuthenticatedUser = Depends(current_user)) -> None:
    try:
        deleted = await delete_document(document_id=str(document_id), token=user.access_token)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Document store unavailable") from exc
    if not deleted:
        raise HTTPException(status_code=403, detail="Document cannot be deleted")


@router.post("/admin/ingest/cocktails", status_code=status.HTTP_202_ACCEPTED)
async def ingest_cocktail_documents(
    request: CocktailIngestRequest,
    admin_key: str | None = Header(default=None, alias="X-Admin-Ingest-Key"),
) -> dict[str, Any]:
    if not settings.ADMIN_INGEST_KEY or admin_key != settings.ADMIN_INGEST_KEY:
        raise HTTPException(status_code=403, detail="Administrative authorization required")
    try:
        count = await ingest_cocktails(letters=request.letters, limit=request.limit)
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail="Cocktail provider or embedding service unavailable") from exc
    return {"status": "accepted", "requested": request.limit, "ingested": count}
