from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.services.campaign_service import CampaignService
from app.schemas.campaign import CampaignCreate, CampaignOut, CampaignUpdate, StartCampaignRequest
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

def get_campaign_service(db=Depends(get_db)) -> CampaignService:
    return CampaignService(db)

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
    """Retorna o status da campanha ativa do usuário"""
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
            await service.seed_campaigns(user_id=current_user_id)
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
    campaign = await service.update_campaign(
        campaign_id, 
        CampaignUpdate(status="cancelled", cancelled_at=datetime.now()),
        user_id=current_user_id
    )
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    return {
        "success": True,
        "message": "Campanha cancelada com sucesso"
    }

@router.put("/{campaign_id}/complete-chapter", response_model=dict)
async def complete_chapter(
    campaign_id: str,
    request: dict,
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Marca um capítulo como completo"""
    chapter = request.get("chapter_completed")
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Capítulo não informado"
        )
    
    campaign = await service.complete_chapter(campaign_id, chapter, user_id=current_user_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    return {
        "success": True,
        "message": f"Capítulo {chapter} completado!",
        "campaign": campaign
    }

@router.post("/seed", response_model=dict)
async def seed_campaigns(
    current_user_id: str = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service)
):
    """Popula o banco com campanhas base para o usuário"""
    try:
        campaigns = await service.seed_campaigns(user_id=current_user_id)
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