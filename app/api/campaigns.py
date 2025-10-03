from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.services.campaign_service import CampaignService
from app.services.vector_store_service import VectorStoreService
from app.schemas.campaign import CampaignCreate, CampaignOut, CampaignUpdate, StartCampaignRequest
from app.api.auth import get_current_user
from app.core.dependencies import get_campaign_service, get_vector_store_service
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class CompleteChapterRequest(BaseModel):
    character_id: str
    chapter_completed: int

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

@router.get("/", response_model=dict)
async def get_campaigns(
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Retorna todas as campanhas do usuário autenticado"""
    campaigns = await service.get_campaigns(user_id=current_user_id)
    return {
        "campaigns": campaigns,
        "total": len(campaigns)
    }

@router.get("/active/status", response_model=dict)
async def get_active_campaign_status(
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Retorna o status da campanha ativa do usuário (apenas in_progress)"""
    active_campaign = await service.get_active_campaign(current_user_id)
    return {
        "has_active_campaign": active_campaign is not None,
        "active_campaign": active_campaign
    }

@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: str,
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Retorna uma campanha específica do usuário"""
    campaign = await service.get_campaign_by_id(campaign_id, user_id=current_user_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    return campaign

@router.post("/", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Cria uma nova campanha para o usuário autenticado"""
    try:
        campaign = await service.create_campaign(campaign_data, user_id=current_user_id)
        return campaign
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/start", response_model=dict)
async def start_campaign(
    request: StartCampaignRequest,
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Inicia uma campanha com o personagem selecionado"""
    try:
        campaign = await service.get_campaign_by_id(request.campaign_id, user_id=current_user_id)
        if not campaign:
            await service.seed_campaigns()
            campaign = await service.get_campaign_by_id(request.campaign_id, user_id=current_user_id)
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha não encontrada"
            )
        
        updated_campaign = await service.start_campaign(
            campaign_id=request.campaign_id,
            character_id=request.character_id,
            character_name=request.character_name,
            user_id=current_user_id
        )
        
        return {
            "success": True,
            "message": f"Campanha '{updated_campaign.title}' iniciada com sucesso!",
            "campaign": updated_campaign
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: str,
    update_data: CampaignUpdate,
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Atualiza uma campanha do usuário"""
    campaign = await service.update_campaign(campaign_id, update_data, user_id=current_user_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    return campaign

@router.delete("/{campaign_id}/cancel", response_model=dict)
async def cancel_campaign(
    campaign_id: str,
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Cancela uma campanha ativa"""
    success = await service.cancel_campaign(campaign_id, user_id=current_user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada ou não está em progresso"
        )
    
    return {
        "success": True,
        "message": "Campanha cancelada com sucesso"
    }

@router.put("/{campaign_id}/complete-chapter", summary="Completar capítulo")
async def complete_chapter(
    campaign_id: str,
    request: CompleteChapterRequest,
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user_id: str = Depends(get_current_user)
):
    """
    Completa capítulo: extrai lore, arquiva, limpa current.
    Marca como completed e libera personagem.
    """
    try:
        result = await campaign_service.complete_chapter(
            campaign_id=campaign_id,
            chapter=request.chapter_completed,
            user_id=current_user_id
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Campanha não encontrada ou erro ao completar"
            )
        
        logger.info(f"✓ Capítulo {request.chapter_completed} completado com sucesso")
        
        return {
            "success": True,
            "message": f"Capítulo {request.chapter_completed} completado!",
            "redirect_to_campaigns": True
        }
        
    except Exception as e:
        logger.error(f"Erro ao completar capítulo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seed", response_model=dict)
async def seed_campaigns(
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Popula o banco com campanhas base"""
    try:
        campaigns = await service.seed_campaigns()
        return {
            "success": True,
            "message": f"{len(campaigns)} campanhas criadas com sucesso!",
            "campaigns": campaigns
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/world-lore/summary", response_model=Dict[str, Any])
async def get_world_lore_summary(
    current_user_id: str = Depends(get_current_user)
):
    """Retorna resumo do World Lore acumulado"""
    try:
        vector_store = VectorStoreService()
        lore_summary = vector_store.get_world_lore_summary()
        
        return {
            "success": True,
            "lore": lore_summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar world lore: {str(e)}"
        )