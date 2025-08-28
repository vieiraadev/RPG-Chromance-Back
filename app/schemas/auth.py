from pydantic import BaseModel, EmailStr, validator
import re

class SignupRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    
    @validator('nome')
    def validate_nome(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Nome deve ter pelo menos 2 caracteres')
        if len(v.strip()) > 100:
            raise ValueError('Nome não pode ter mais de 100 caracteres')
        return v.strip()
    
    @validator('senha')
    def validate_senha(cls, v):
        if len(v) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserOut(BaseModel):
    id: str
    nome: str
    email: str