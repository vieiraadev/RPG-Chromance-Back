from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from app.api.auth import router as auth_router
from app.api.characters import router as chars_router
from app.api.campaigns import router as campaigns_router
from app.api.llm import router as llm_router
from app.core.database import get_db, mongodb
from app.core.middleware import setup_middlewares

app = FastAPI(
    title="RPG Chromance API — Cyberpunk",
    version="0.1.0",
    description="Contrato inicial (Auth, Personagem, Campanha, Histórico, Ação e LLM).",
)

# aplica middlewares (CORS)
setup_middlewares(app)

# grupos de rotas
app.include_router(auth_router)
app.include_router(chars_router)
app.include_router(campaigns_router)
app.include_router(llm_router)