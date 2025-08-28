import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.database import get_database
from app.core.security import get_password_hash
from app.models.user import UserModel, UserResponse

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.users
        self.collection.create_index("email", unique=True)

    async def create_user(self, nome: str, email: str, senha: str) -> UserResponse:
        """Cria um novo usuário"""
        try:
            if await self.get_user_by_email(email):
                raise ValueError("Email já está em uso")

            senha_hash = get_password_hash(senha)

            user_data = {
                "nome": nome,
                "email": email,
                "senha_hash": senha_hash,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "ativo": True,
            }

            result = self.collection.insert_one(user_data)

            user = self.collection.find_one({"_id": result.inserted_id})

            return self._user_document_to_response(user)

        except DuplicateKeyError:
            raise ValueError("Email já está em uso")
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            raise ValueError("Erro interno do servidor")

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        return self.collection.find_one({"email": email})

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Busca usuário por ID"""
        try:
            user = self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                return self._user_document_to_response(user)
            return None
        except Exception:
            return None

    def _user_document_to_response(self, user_doc: Dict[str, Any]) -> UserResponse:
        """Converte documento do MongoDB para UserResponse"""
        return UserResponse(
            id=str(user_doc["_id"]),
            nome=user_doc["nome"],
            email=user_doc["email"],
            created_at=user_doc["created_at"],
            ativo=user_doc["ativo"],
        )
