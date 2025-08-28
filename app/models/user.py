from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer


class UserModel(BaseModel):
    """Modelo do usuário para o MongoDB"""

    nome: str
    email: EmailStr
    senha_hash: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    ativo: bool = True

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        """Serializa datetime para ISO format"""
        return value.isoformat()

    @field_serializer("id", check_fields=False)
    def serialize_object_id(self, value: ObjectId) -> str:
        """Serializa ObjectId para string"""
        return str(value) if isinstance(value, ObjectId) else value


class UserResponse(BaseModel):
    """Modelo de resposta do usuário (sem senha)"""

    id: str
    nome: str
    email: str
    created_at: datetime
    ativo: bool

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> str:
        """Serializa datetime para ISO format"""
        return value.isoformat()
