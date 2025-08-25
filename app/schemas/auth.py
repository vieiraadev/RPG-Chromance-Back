from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class SignupRequest(BaseModel):
    nome: str = Field(..., examples=["Vitor"])
    email: EmailStr = Field(..., examples=["vitor@neon.city"])
    senha: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

class UserOut(BaseModel):
    id: str
    nome: str
    email: EmailStr
