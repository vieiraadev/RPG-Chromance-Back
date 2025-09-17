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

@app.get("/liveness", include_in_schema=False)
async def liveness():
    return {"status": "alive"}

@app.get("/readiness", include_in_schema=False)
async def readiness():
    try:
        db = get_db()
        await db.command("ping")
        return {"status": "ready", "deps": {"mongo": "ok"}}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "deps": {"mongo": "fail"},
                "detail": str(e)[:120],
            },
        )

@app.get("/health", tags=["Infra"])
async def health():
    try:
        db = get_db()
        await db.command("ping")
        from app.config import OPENAI_API_KEY
        llm_status = "ok" if OPENAI_API_KEY else "not_configured"
        
        return {
            "ok": True,
            "db": "ok",
            "llm": llm_status
        }
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "db": "fail",
                "llm": "unknown"
            },
        )