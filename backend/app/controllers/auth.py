from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.dependencies import AuthenticatedUser, current_user
from app.services.supabase_auth import SupabaseAuthError, sign_in, sign_out, sign_up

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class UserSummary(BaseModel):
    id: str
    email: str | None = None


class RegisterResponse(BaseModel):
    user: UserSummary
    session: dict[str, Any] | None = None
    email_confirmation_required: bool


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    user: UserSummary


def _user_summary(payload: dict[str, Any]) -> UserSummary:
    user = payload.get("user") or payload
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=502, detail="Supabase returned an invalid user")
    return UserSummary(id=str(user_id), email=user.get("email"))


def _supabase_error(exc: SupabaseAuthError, *, register: bool = False) -> HTTPException:
    if register and (exc.status_code == 409 or "already registered" in exc.message.lower()):
        return HTTPException(status_code=409, detail="User already exists")
    if exc.status_code in (400, 422):
        return HTTPException(status_code=400, detail=exc.message)
    if exc.status_code in (401, 403):
        return HTTPException(status_code=401, detail="Invalid credentials")
    return HTTPException(status_code=503, detail="Supabase Auth is unavailable")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(credentials: Credentials) -> RegisterResponse:
    try:
        payload = await sign_up(credentials.email, credentials.password)
    except SupabaseAuthError as exc:
        raise _supabase_error(exc, register=True) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Supabase Auth is unavailable") from exc

    session = payload.get("session")
    return RegisterResponse(
        user=_user_summary(payload),
        session=session,
        email_confirmation_required=session is None,
    )


@router.post("/login", response_model=LoginResponse)
async def login_user(credentials: Credentials) -> LoginResponse:
    try:
        payload = await sign_in(credentials.email, credentials.password)
    except SupabaseAuthError as exc:
        raise _supabase_error(exc) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Supabase Auth is unavailable") from exc

    return LoginResponse(
        access_token=payload.get("access_token", ""),
        refresh_token=payload.get("refresh_token", ""),
        token_type=payload.get("token_type", "bearer"),
        expires_in=payload.get("expires_in"),
        user=_user_summary(payload),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def logout_user(user: AuthenticatedUser = Depends(current_user)) -> Response:
    try:
        await sign_out(user.access_token)
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=503, detail="Supabase Auth is unavailable") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Supabase Auth is unavailable") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
