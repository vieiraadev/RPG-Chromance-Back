import logging

from pymongo import MongoClient
from pymongo.database import Database

from app.config import MONGO_DB, MONGO_URI

logger = logging.getLogger(__name__)


class MongoDB:
    _instance = None
    _client = None
    _database = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()

    def connect(self):
        """Conecta ao MongoDB"""
        try:
            self._client = MongoClient(MONGO_URI)
            self._database = self._client[MONGO_DB]
            self._client.admin.command("ping")
            logger.info(f"Conectado ao MongoDB: {MONGO_DB}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao MongoDB: {e}")
            raise

    @property
    def client(self) -> MongoClient:
        return self._client

    @property
    def database(self) -> Database:
        return self._database

    def close(self):
        """Fecha a conexão"""
        if self._client:
            self._client.close()


mongodb = MongoDB()


def get_database() -> Database:
    """Retorna a instância do database"""
    return mongodb.database


def get_db() -> Database:
    """Função compatível com main.py existente"""
    return mongodb.database
