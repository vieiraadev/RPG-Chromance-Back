from fastapi import FastAPI
from app.core.database import get_db

app = FastAPI()

@app.get("/health")
async def health():
    db = get_db()
    doc = await db.health.find_one({})
    return {"ok": True, "has_health_doc": doc is not None}
