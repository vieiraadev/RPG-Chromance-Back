# app/main.py
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from app.core.database import get_db
from app.api.auth import router as auth_router
from app.api.characters import router as chars_router
from app.api.campaigns import router as camp_router

app = FastAPI(
    title="RPG Chromance API — Cyberpunk",
    version="0.1.0",
    description="Contrato inicial (Auth, Personagem, Campanha, Histórico e Ação).",
)

# ---- registrando grupos de rotas ----
app.include_router(auth_router)
app.include_router(chars_router)
app.include_router(camp_router)

# ---- seus endpoints de saúde (mantidos) ----
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
            content={"status": "not_ready", "deps": {"mongo": "fail"}, "detail": str(e)[:120]},
        )

@app.get("/health", tags=["Infra"])
async def health():
    try:
        db = get_db()
        await db.command("ping")
        return {"ok": True, "db": "ok"}
    except Exception:
        return JSONResponse(status_code=503, content={"ok": False, "db": "fail"})
