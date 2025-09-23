from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.schemas.llm import (
    LLMChatRequest,
    LLMChatResponse,
    CharacterSuggestionRequest,
    LLMHealthCheck,
    ContextualAction
)
from app.services.llm_service import LLMService
from app.services.character_service import CharacterService
from app.services.campaign_service import CampaignService
from app.repositories.character_repo import CharacterRepository
from app.core.database import get_database
from app.api.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["LLM"])

def get_llm_service() -> LLMService:
    return LLMService()

def get_character_service(db = Depends(get_database)) -> CharacterService:
    """Dependency injection para o serviço de personagens"""
    repository = CharacterRepository(db)
    return CharacterService(repository)

def get_campaign_service(db = Depends(get_database)) -> CampaignService:
    """Dependency injection para o serviço de campanhas"""
    return CampaignService(db)

@router.post("/chat", response_model=LLMChatResponse, summary="Chat com LLM")
async def chat_with_llm(
    request: LLMChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    character_service: CharacterService = Depends(get_character_service),
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user_id: str = Depends(get_current_user)
):
    """
    Envia mensagem para a LLM e retorna resposta com ações contextuais.
    Inclui contexto do personagem e campanha ativa.
    """
    try:
        character_context = None
        campaign_context = None
        
        try:
            active_campaign = await campaign_service.get_active_campaign(current_user_id)
            if active_campaign:
                chapter_field = getattr(active_campaign, 'chapter', None)
                current_chapter_field = getattr(active_campaign, 'current_chapter', None)
                title_field = getattr(active_campaign, 'title', 'SEM_TITULO')
                current_chapter = None
                try:
                    ch_val = int(chapter_field) if chapter_field else 0
                    curr_ch_val = int(current_chapter_field) if current_chapter_field else 0
                    
                    if ch_val > 0 and curr_ch_val > 0:
                        current_chapter = max(ch_val, curr_ch_val)
                    elif ch_val > 0:
                        current_chapter = ch_val
                    elif curr_ch_val > 0:
                        current_chapter = curr_ch_val
                    else:
                        current_chapter = 1
                        
                except (ValueError, TypeError):
                    current_chapter = 1

                campaign_context = {
                    "campaign_id": active_campaign.campaign_id,
                    "title": title_field,
                    "chapter": chapter_field,
                    "current_chapter": current_chapter,
                    "description": getattr(active_campaign, 'description', ''),
                    "full_description": getattr(active_campaign, 'full_description', '')
                }
                
                logger.info(f"Contexto da campanha carregado: {title_field} - Capítulo {current_chapter}")
                
        except Exception as campaign_error:
            logger.error(f"Erro ao carregar campanha ativa: {campaign_error}")
        
        if request.character_id:
            try:
                character = await character_service.get_character(request.character_id, current_user_id)
                if character:
                    atributos_data = {}
                    if hasattr(character, 'atributos') and character.atributos:
                        if hasattr(character.atributos, 'vida'):
                            atributos_data = {
                                "vida": character.atributos.vida,
                                "energia": character.atributos.energia,
                                "forca": character.atributos.forca,
                                "inteligencia": character.atributos.inteligencia
                            }
                        elif isinstance(character.atributos, dict):
                            atributos_data = {
                                "vida": character.atributos.get('vida', 20),
                                "energia": character.atributos.get('energia', 20),
                                "forca": character.atributos.get('forca', 10),
                                "inteligencia": character.atributos.get('inteligencia', 10)
                            }
                    else:
                        atributos_data = {
                            "vida": 20,
                            "energia": 20,
                            "forca": 10,
                            "inteligencia": 10
                        }
                    
                    character_context = {
                        "nome": character.name,
                        "raca": character.raca,
                        "classe": character.classe,
                        "descricao": character.descricao,
                        "atributos": atributos_data
                    }
                    logger.info(f"Contexto do personagem carregado: {character.name} ({character.raca} {character.classe})")
                else:
                    logger.warning(f"Personagem {request.character_id} não encontrado para o usuário {current_user_id}")
            except Exception as char_error:
                logger.error(f"Erro ao carregar personagem: {char_error}")

        history = []
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        result = await llm_service.chat_with_llm(
            message=request.message,
            character_context=character_context,
            campaign_context=campaign_context,
            conversation_history=history,
            generate_actions=request.generate_actions
        )

        contextual_actions = []
        if result.get("contextual_actions"):
            for action in result["contextual_actions"]:
                contextual_actions.append(ContextualAction(**action))

        return LLMChatResponse(
            success=result["success"],
            response=result.get("response"),
            contextual_actions=contextual_actions,
            error=result.get("error"),
            usage=result.get("usage")
        )

    except Exception as e:
        logger.error(f"Erro no chat LLM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no chat: {str(e)}"
        )

@router.post("/character-suggestion", response_model=LLMChatResponse, summary="Sugestão de personagem")
async def suggest_character(
    request: CharacterSuggestionRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Gera sugestões para criação/melhoria de personagem usando LLM
    """
    try:
        result = await llm_service.generate_character_suggestion(request.partial_data)
        return LLMChatResponse(**result)

    except Exception as e:
        logger.error(f"Erro na sugestão de personagem: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar sugestão: {str(e)}"
        )

@router.get("/health", response_model=LLMHealthCheck, summary="Health check da LLM")
async def llm_health_check(
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Verifica se a LLM está disponível
    """
    try:
        result = await llm_service.test_connection()
        return LLMHealthCheck(
            status="healthy" if result["success"] else "unhealthy",
            model=result["model"],
            available=result["success"]
        )

    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return LLMHealthCheck(
            status="unhealthy",
            model="unknown",
            available=False
        )