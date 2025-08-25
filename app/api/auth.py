from fastapi import APIRouter
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/signup", response_model=TokenResponse, summary="Criar conta")
async def signup(body: SignupRequest):
    return TokenResponse(access_token="demo-token")

@router.post("/login", response_model=TokenResponse, summary="Autenticar e retornar JWT")
async def login(body: LoginRequest):
    return TokenResponse(access_token="demo-token")

@router.get("/me", response_model=UserOut, summary="Dados do usuário autenticado")
async def me():
    return UserOut(id="u1", nome="Vitor", email="vitor@neon.city")
