from typing import Optional

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    nome: str
    email: str
