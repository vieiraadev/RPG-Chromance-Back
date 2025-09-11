import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token
from app.schemas.auth import (
    LoginRequest, 
    SignupRequest, 
    TokenResponse, 
    RefreshTokenRequest,
    UserOut,
    UpdateProfileRequest
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Auth"])
auth_service = AuthService()
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Dependency para obter usuário atual do token com segurança aprimorada"""
    if not credentials or not credentials.credentials:
        logger.warning("Tentativa de acesso sem token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials)
    if not payload:
        logger.warning("Tentativa de acesso com token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token sem user_id válido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id

@router.post(
    "/signup", 
    response_model=TokenResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova conta"
)
async def signup(body: SignupRequest):
    """
    Endpoint para criar nova conta com validações de segurança:
    - Validação de força da senha
    - Validação de formato de email
    - Verificação de email duplicado
    - Rate limiting básico
    """
    try:
        result = await auth_service.signup(body)
        logger.info(f"Nova conta criada: {body.email}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no signup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post(
    "/login", 
    response_model=TokenResponse, 
    summary="Autenticar e retornar JWT"
)
async def login(body: LoginRequest):
    """
    Endpoint para login com medidas de segurança:
    - Verificação de usuário ativo
    - Delay contra timing attacks
    - Logging de tentativas suspeitas
    - Retorna access + refresh token
    """
    try:
        result = await auth_service.login(body)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post(
    "/refresh", 
    response_model=TokenResponse, 
    summary="Renovar token de acesso"
)
async def refresh_token(body: RefreshTokenRequest):
    """
    Endpoint para renovar access token usando refresh token:
    - Verifica validade do refresh token
    - Confirma que usuário ainda está ativo
    - Gera novo access token
    """
    try:
        result = await auth_service.refresh_access_token(body.refresh_token)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get(
    "/me", 
    response_model=UserOut, 
    summary="Dados do usuário autenticado"
)
async def get_user_profile(current_user_id: str = Depends(get_current_user)):
    """
    Endpoint para obter dados do usuário atual:
    - Verifica token válido
    - Confirma que usuário existe e está ativo
    - Retorna dados básicos (sem informações sensíveis)
    """
    try:
        user = await auth_service.get_current_user(current_user_id)
        if not user:
            logger.warning(f"Usuário não encontrado ou inativo: {current_user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return UserOut(id=user.id, nome=user.nome, email=user.email)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put(
    "/profile", 
    response_model=UserOut, 
    summary="Atualizar dados do usuário autenticado"
)
async def update_user_profile(
    update_data: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user)
):
    """
    Endpoint para atualizar dados do usuário atual:
    - Verifica token válido
    - Permite alterar nome, email e senha
    - Valida se novo email não está em uso por outro usuário
    - Retorna dados atualizados
    """
    try:
        updated_user = await auth_service.update_user_profile(current_user_id, update_data)
        
        if not updated_user:
            logger.warning(f"Falha ao atualizar usuário: {current_user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível atualizar o perfil"
            )
        
        logger.info(f"Perfil atualizado com sucesso: {updated_user.email}")
        return UserOut(id=updated_user.id, nome=updated_user.nome, email=updated_user.email)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao atualizar perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post(
    "/logout", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Fazer logout (invalidar token)"
)
async def logout(current_user_id: str = Depends(get_current_user)):
    """
    Endpoint para logout:
    - Em uma implementação completa, adicionaria o token a uma blacklist
    - Por enquanto, apenas confirma que o usuário está autenticado
    - Cliente deve descartar os tokens localmente
    """
    logger.info(f"Logout realizado para usuário: {current_user_id}")
    return {"message": "Logout realizado com sucesso"}