from typing import Generator
from app.core.database import get_db
from app.services.campaign_service import CampaignService
from app.services.vector_store_service import VectorStoreService
from fastapi import Depends

def get_vector_store_service() -> VectorStoreService:
    """Retorna instância do VectorStoreService"""
    return VectorStoreService()

def get_campaign_service(
    db = Depends(get_db),
    vector_store: VectorStoreService = Depends(get_vector_store_service)
) -> CampaignService:
    """Retorna instância do CampaignService com dependências injetadas"""
    return CampaignService(db, vector_store)