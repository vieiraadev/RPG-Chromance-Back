from datetime import timedelta
from typing import Optional

from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password
from app.models.user import UserResponse
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def signup(self, signup_data: SignupRequest) -> TokenResponse:
        """Registra um novo usuário"""
        try:
            user = await self.user_repo.create_user(
                nome=signup_data.nome, email=signup_data.email, senha=signup_data.senha
            )

            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.id, "email": user.email}, expires_delta=access_token_expires
            )

            return TokenResponse(access_token=access_token, token_type="bearer")

        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError("Erro interno do servidor")

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        """Autentica um usuário"""
        user_doc = await self.user_repo.get_user_by_email(login_data.email)

        if not user_doc or not verify_password(login_data.senha, user_doc["senha_hash"]):
            raise ValueError("Email ou senha incorretos")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user_doc["_id"]), "email": user_doc["email"]}, expires_delta=access_token_expires
        )

        return TokenResponse(access_token=access_token, token_type="bearer")

    async def get_current_user(self, user_id: str) -> Optional[UserResponse]:
        """Busca dados do usuário atual"""
        return await self.user_repo.get_user_by_id(user_id)
