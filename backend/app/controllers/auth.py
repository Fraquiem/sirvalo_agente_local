from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register_user(user: UserRegister):
    # TODO: Implementar registro con Supabase Auth
    return {"message": "Registro exitoso", "email": user.email}

@router.post("/login")
async def login_user(user: UserLogin):
    # TODO: Implementar login con Supabase Auth y retornar JWT
    return {"access_token": "mock-token-from-supabase", "token_type": "bearer"}
