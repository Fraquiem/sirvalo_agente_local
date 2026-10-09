"""Small REST adapter for Supabase database and pgvector operations."""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


def _url(table: str) -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/{table}"


def _headers(*, token: str | None = None, service: bool = False) -> dict[str, str]:
    key = settings.SUPABASE_SERVICE_ROLE_KEY if service else settings.SUPABASE_ANON_KEY
    return {"apikey": key, "Authorization": f"Bearer {token or key}", "Content-Type": "application/json", "Prefer": "return=representation"}


async def create_or_update_document(*, owner_id: str | None, source_type: str, source_uri: str | None, external_id: str | None, filename: str | None, mime_type: str | None, size_bytes: int | None, title: str | None, checksum: str | None, metadata: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        params: dict[str, str] = {"select": "*"}
        if source_type == "cocktaildb":
            params["external_id"] = f"eq.{external_id}"
            params["source_type"] = "eq.cocktaildb"
        else:
            params["owner_id"] = f"eq.{owner_id}"
            params["checksum"] = f"eq.{checksum}"
            params["source_type"] = "eq.upload"
        existing = await client.get(_url("documents"), headers=_headers(service=True), params=params)
        existing.raise_for_status()
        payload = {"owner_id": owner_id, "source_type": source_type, "source_uri": source_uri, "external_id": external_id, "filename": filename, "mime_type": mime_type, "size_bytes": size_bytes, "title": title, "checksum": checksum, "status": "processing", "error_message": None, "metadata": metadata}
        if existing.json():
            document_id = existing.json()[0]["id"]
            response = await client.patch(f"{_url('documents')}?id=eq.{document_id}", headers=_headers(service=True), json=payload)
        else:
            response = await client.post(_url("documents"), headers=_headers(service=True), json=payload)
        response.raise_for_status()
        return response.json()[0]


async def replace_chunks(document_id: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        deleted = await client.delete(f"{_url('document_chunks')}?document_id=eq.{document_id}", headers=_headers(service=True))
        deleted.raise_for_status()
        if chunks:
            inserted = await client.post(_url("document_chunks"), headers=_headers(service=True), json=chunks)
            inserted.raise_for_status()
        updated = await client.patch(f"{_url('documents')}?id=eq.{document_id}", headers=_headers(service=True), json={"status": "ready", "error_message": None})
        updated.raise_for_status()
        return updated.json()[0]


async def mark_document_error(document_id: str, message: str) -> None:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.patch(f"{_url('documents')}?id=eq.{document_id}", headers=_headers(service=True), json={"status": "error", "error_message": message[:500]})
        response.raise_for_status()


async def list_documents(*, token: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.get(_url("documents"), headers=_headers(token=token), params={"select": "id,title,filename,source_type,source_uri,status,created_at,updated_at,metadata", "order": "created_at.desc"})
        response.raise_for_status()
        return response.json()


async def get_document(*, document_id: str, token: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.get(_url("documents"), headers=_headers(token=token), params={"id": f"eq.{document_id}", "select": "*"})
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None


async def delete_document(*, document_id: str, token: str) -> bool:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.delete(f"{_url('documents')}?id=eq.{document_id}", headers=_headers(token=token), params={"select": "id"})
        response.raise_for_status()
        return bool(response.json())


async def search_similar_chunks(query_embedding: list[float], *, token: str, limit: int = 5, threshold: float = 0.0) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.post(f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/rpc/match_documents", headers=_headers(token=token), json={"query_embedding": query_embedding, "match_threshold": threshold, "match_count": min(max(limit, 1), 20)})
        response.raise_for_status()
        return response.json()


async def create_conversation(*, title: str, user_id: str, token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.post(
            _url("conversations"),
            headers=_headers(token=token),
            json={"user_id": user_id, "title": title[:120]},
        )
        response.raise_for_status()
        return response.json()[0]


async def get_conversation(*, conversation_id: str, token: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.get(
            _url("conversations"),
            headers=_headers(token=token),
            params={"id": f"eq.{conversation_id}", "select": "id,user_id,title,created_at,updated_at"},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None


async def list_conversations(*, token: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.get(
            _url("conversations"),
            headers=_headers(token=token),
            params={"select": "id,title,created_at,updated_at", "order": "updated_at.desc"},
        )
        response.raise_for_status()
        return response.json()


async def list_messages(*, conversation_id: str, token: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.get(
            _url("messages"),
            headers=_headers(token=token),
            params={
                "conversation_id": f"eq.{conversation_id}",
                "select": "id,role,content,sources,created_at",
                "order": "created_at.asc",
            },
        )
        response.raise_for_status()
        return response.json()


async def save_message(*, conversation_id: str, role: str, content: str, sources: list[dict[str, Any]], token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=settings.SUPABASE_TIMEOUT_SECONDS) as client:
        response = await client.post(
            _url("messages"),
            headers=_headers(token=token),
            json={"conversation_id": conversation_id, "role": role, "content": content, "sources": sources},
        )
        response.raise_for_status()
        return response.json()[0]
