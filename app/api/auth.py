import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.security import verify_token
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserOut
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Auth"])
auth_service = AuthService()


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Dependency para obter usuário atual do token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization.split(" ")[1]
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    return payload.get("sub")


@router.post("/signup", response_model=TokenResponse, summary="Criar conta")
async def signup(body: SignupRequest):
    """Endpoint para criar nova conta"""
    try:
        result = await auth_service.signup(body)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro no signup: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/login", response_model=TokenResponse, summary="Autenticar e retornar JWT")
async def login(body: LoginRequest):
    """Endpoint para login"""
    try:
        result = await auth_service.login(body)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/me", response_model=UserOut, summary="Dados do usuário autenticado")
async def me(current_user_id: str = Depends(get_current_user)):
    """Endpoint para obter dados do usuário atual"""
    user = await auth_service.get_current_user(current_user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return UserOut(id=user.id, nome=user.nome, email=user.email)
