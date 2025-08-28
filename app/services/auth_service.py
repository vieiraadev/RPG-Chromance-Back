import logging
from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    create_access_token, 
    create_refresh_token,
    verify_password, 
    SecurityService
)
from app.models.user import UserResponse
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.security = SecurityService()

    async def signup(self, signup_data: SignupRequest) -> TokenResponse:
        """Registra um novo usuário com validações de segurança"""
        try:
            validated_email = self.security.validate_email_format(signup_data.email)
            validated_nome = self.security.validate_name(signup_data.nome)
            
            existing_user = await self.user_repo.get_user_by_email(validated_email)
            if existing_user:
                logger.warning(f"Tentativa de registro com email já existente: {validated_email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email já está em uso"
                )
            
            user = await self.user_repo.create_user(
                nome=validated_nome, 
                email=validated_email, 
                senha=signup_data.senha
            )
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.id, "email": user.email}, 
                expires_delta=access_token_expires
            )
            refresh_token = create_refresh_token(user.id)
            
            logger.info(f"Usuário criado com sucesso: {user.email}")
            
            return TokenResponse(
                access_token=access_token, 
                refresh_token=refresh_token,
                token_type="bearer"
            )
            
        except HTTPException:
            raise
        except ValueError as e:
            logger.error(f"Erro de validação no signup: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Erro interno no signup: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor"
            )

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        """Autentica um usuário com medidas de segurança"""
        try:
            validated_email = self.security.validate_email_format(login_data.email)
            
            user_doc = await self.user_repo.get_user_by_email(validated_email)
            
            if not user_doc or not user_doc.get("ativo", True):
                logger.warning(f"Tentativa de login com usuário inexistente/inativo: {validated_email}")
                import asyncio
                await asyncio.sleep(0.1)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou senha incorretos"
                )
            
            if not verify_password(login_data.senha, user_doc["senha_hash"]):
                logger.warning(f"Tentativa de login com senha incorreta: {validated_email}")
                import asyncio
                await asyncio.sleep(0.1)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou senha incorretos"
                )

            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user_doc["_id"]), "email": user_doc["email"]}, 
                expires_delta=access_token_expires
            )
            refresh_token = create_refresh_token(str(user_doc["_id"]))
            
            logger.info(f"Login bem-sucedido: {validated_email}")
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token, 
                token_type="bearer"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro interno no login: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor"
            )

    async def get_current_user(self, user_id: str) -> Optional[UserResponse]:
        """Busca dados do usuário atual com verificações de segurança"""
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            
            if user and not user.ativo:
                logger.warning(f"Tentativa de acesso com usuário inativo: {user_id}")
                return None
                
            return user
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário atual: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Renova token de acesso usando refresh token"""
        from app.core.security import verify_refresh_token
        
        try:
            user_id = verify_refresh_token(refresh_token)
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token inválido"
                )
            
            user = await self.get_current_user(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuário não encontrado ou inativo"
                )
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.id, "email": user.email}, 
                expires_delta=access_token_expires
            )
            
            logger.info(f"Token renovado para usuário: {user.email}")
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token, 
                token_type="bearer"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao renovar token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor"
            )