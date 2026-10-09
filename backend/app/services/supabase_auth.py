"""Small, anon-key-only adapter for Supabase Auth HTTP endpoints."""

from typing import Any

import httpx

from app.config import settings


class SupabaseAuthError(Exception):
    """An error returned by Supabase Auth."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _auth_headers(access_token: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
        return str(payload.get("msg") or payload.get("error_description") or payload.get("message") or "Supabase Auth request failed")
    except ValueError:
        return "Supabase Auth request failed"


async def sign_up(email: str, password: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/signup",
            headers=_auth_headers(),
            json={"email": email, "password": password},
        )
    if response.status_code >= 400:
        raise SupabaseAuthError(response.status_code, _error_message(response))
    return response.json()


async def sign_in(email: str, password: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password",
            headers=_auth_headers(),
            json={"email": email, "password": password},
        )
    if response.status_code >= 400:
        raise SupabaseAuthError(response.status_code, _error_message(response))
    return response.json()


async def get_user(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
            headers=_auth_headers(access_token),
        )
    if response.status_code >= 400:
        raise SupabaseAuthError(response.status_code, _error_message(response))
    return response.json()


async def sign_out(access_token: str) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/logout",
            headers=_auth_headers(access_token),
        )
    if response.status_code >= 400:
        raise SupabaseAuthError(response.status_code, _error_message(response))
