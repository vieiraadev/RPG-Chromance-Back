from motor.motor_asyncio import AsyncIOMotorClient
from .. import config

_client: AsyncIOMotorClient | None = None
_db = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(config.MONGO_URI)
    return _client

def get_db():
    global _db
    if _db is None:
        _db = get_client().get_database(config.MONGO_DB)
    return _db
