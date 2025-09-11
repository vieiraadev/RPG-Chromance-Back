from pydantic import BaseModel, EmailStr, validator, Field, ConfigDict
from typing import Optional
from datetime import datetime
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
    created_at: datetime

class UpdateProfileRequest(BaseModel):
    """Schema para atualização de perfil do usuário"""
    nome: str = Field(..., min_length=2, max_length=100, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="Email do usuário")
    senha: Optional[str] = Field(None, min_length=6, max_length=100, description="Nova senha (opcional)")
    
    @validator('nome')
    def validate_nome(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Nome deve ter pelo menos 2 caracteres')
        if len(v.strip()) > 100:
            raise ValueError('Nome não pode ter mais de 100 caracteres')
        return v.strip()
    
    @validator('senha')
    def validate_senha(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "João Silva Santos",
                "email": "joao.santos@email.com",
                "senha": "novaSenha123"
            }
        }
    )