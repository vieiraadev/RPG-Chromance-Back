from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.schemas.llm import (
    LLMChatRequest,
    LLMChatResponse,
    ContextualAction,
    ProgressionResetResponse
)
from app.services.llm_service import LLMService
from app.services.character_service import CharacterService
from app.services.campaign_service import CampaignService
from app.services.vector_store_service import VectorStoreService
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
    """Dependency injection para o serviço de campanhas com VectorStore"""
    vector_store = VectorStoreService()
    return CampaignService(db, vector_store_service=vector_store)

def get_vector_store_service() -> VectorStoreService:
    return VectorStoreService()

@router.post("/chat", response_model=LLMChatResponse, summary="Chat com LLM com progressão")
async def chat_with_llm(
    request: LLMChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    character_service: CharacterService = Depends(get_character_service),
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user_id: str = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Envia mensagem para a LLM com sistema de progressão narrativa (10 interações)
    e detecção automática de recompensas
    """
    try:
        character_context = None
        campaign_context = None
        campaign_id = None
        current_chapter = 1

        try:
            active_campaign = await campaign_service.get_active_campaign(current_user_id)
            if active_campaign:
                chapter_field = getattr(active_campaign, 'chapter', None)
                current_chapter_field = getattr(active_campaign, 'current_chapter', None)
                title_field = getattr(active_campaign, 'title', 'SEM_TITULO')
                campaign_id = active_campaign.campaign_id
                
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
                    "campaign_id": campaign_id,
                    "title": title_field,
                    "chapter": chapter_field,
                    "current_chapter": current_chapter,
                    "description": getattr(active_campaign, 'description', ''),
                    "full_description": getattr(active_campaign, 'full_description', ''),
                    "user_id": current_user_id,
                    "_id": campaign_id
                }
                logger.info(f"Contexto da campanha: {title_field} - Capítulo {current_chapter} - Interação {request.interaction_count}/10")
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
                    
                    character_context = {
                        "nome": character.name,
                        "raca": character.raca,
                        "classe": character.classe,
                        "descricao": character.descricao,
                        "atributos": atributos_data,
                        "_id": request.character_id
                    }
                    logger.info(f"Contexto do personagem: {character.name} ({character.raca} {character.classe})")
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
            generate_actions=request.generate_actions,
            interaction_count=request.interaction_count
        )
        
        reward_delivered = None
        if (result.get("success") and 
            request.character_id and 
            campaign_id and 
            request.interaction_count >= 8):
            
            try:
                from app.repositories.character_repo import CharacterRepository
                
                logger.info(f"Tentando detectar recompensa para interação {request.interaction_count}")
                
                character_repo = CharacterRepository(db)
                
                reward_delivered = await llm_service.process_reward_delivery(
                    llm_response=result.get("response", ""),
                    interaction_count=request.interaction_count,
                    chapter=current_chapter,
                    campaign_id=campaign_id,
                    character_repo=character_repo,
                    character_id=request.character_id,
                    user_id=current_user_id
                )
                
                if reward_delivered:
                    logger.info(f"Recompensa '{reward_delivered['name']}' confirmada!")
                    
            except Exception as reward_error:
                logger.error(f"Erro ao processar recompensa: {reward_error}", exc_info=True)

        contextual_actions = []
        if result.get("contextual_actions"):
            for action in result["contextual_actions"]:
                contextual_actions.append(ContextualAction(**action))

        progression_info = result.get("progression")
        if progression_info and reward_delivered:
            progression_info["reward_delivered"] = {
                "name": reward_delivered["name"],
                "description": reward_delivered["description"],
                "type": reward_delivered["type"]
            }
        
        return LLMChatResponse(
            success=result["success"],
            response=result.get("response"),
            contextual_actions=contextual_actions,
            error=result.get("error"),
            usage=result.get("usage"),
            progression=progression_info
        )
                    
    except Exception as e:
        logger.error(f"Erro no chat LLM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no chat: {str(e)}"
        )

@router.post("/reset-progression", response_model=ProgressionResetResponse, summary="Resetar progressão do capítulo")
async def reset_chapter_progression(
    campaign_service: CampaignService = Depends(get_campaign_service),
    current_user_id: str = Depends(get_current_user)
):
    """
    Reseta a progressão do capítulo atual para começar um novo ciclo de 10 interações
    """
    try:
        logger.info(f"Progressão resetada para usuário {current_user_id}")
        return ProgressionResetResponse(
            success=True,
            message="Progressão do capítulo resetada. Novo ciclo de 10 interações iniciado.",
            interaction_count=1
        )
    except Exception as e:
        logger.error(f"Erro ao resetar progressão: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao resetar progressão: {str(e)}"
        )

@router.get("/chroma/campaign/{campaign_id}/history", summary="Histórico de narrativas da campanha")
async def get_campaign_narrative_history(
    campaign_id: str,
    chapter: int = None,
    limit: int = 20,
    vector_store: VectorStoreService = Depends(get_vector_store_service),
    current_user_id: str = Depends(get_current_user)
):
    """Recupera histórico de narrativas de uma campanha"""
    try:
        history = vector_store.get_campaign_history(
            campaign_id=campaign_id,
            chapter=chapter,
            limit=limit
        )
        return {
            "success": True,
            "campaign_id": campaign_id,
            "chapter": chapter,
            "total": len(history),
            "narratives": history
        }
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar histórico: {str(e)}"
        )

@router.get("/chroma/campaign/{campaign_id}/chapter/{chapter}/summary", summary="Resumo do capítulo")
async def get_chapter_summary(
    campaign_id: str,
    chapter: int,
    vector_store: VectorStoreService = Depends(get_vector_store_service),
    current_user_id: str = Depends(get_current_user)
):
    """Retorna resumo completo de um capítulo específico"""
    try:
        summary = vector_store.get_chapter_summary(
            campaign_id=campaign_id,
            chapter=chapter
        )
        return {
            "success": True,
            "campaign_id": campaign_id,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Erro ao gerar resumo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar resumo: {str(e)}"
        )

@router.post("/chroma/search", summary="Busca vetorial de narrativas")
async def search_narratives(
    query: str,
    campaign_id: str = None,
    chapter: int = None,
    n_results: int = 5,
    vector_store: VectorStoreService = Depends(get_vector_store_service),
    current_user_id: str = Depends(get_current_user)
):
    """Busca narrativas similares usando busca vetorial"""
    try:
        results = vector_store.search_similar_narratives(
            query_text=query,
            campaign_id=campaign_id,
            chapter=chapter,
            n_results=n_results
        )
        return {
            "success": True,
            "query": query,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Erro na busca vetorial: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na busca vetorial: {str(e)}"
        )

@router.delete("/chroma/campaign/{campaign_id}", summary="Deletar narrativas da campanha")
async def delete_campaign_narratives(
    campaign_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store_service),
    current_user_id: str = Depends(get_current_user)
):
    """Remove todas as narrativas de uma campanha do ChromaDB"""
    try:
        success = vector_store.delete_campaign_narratives(campaign_id)
        if success:
            return {
                "success": True,
                "message": f"Narrativas da campanha {campaign_id} removidas com sucesso"
            }
        else:
            return {
                "success": False,
                "message": "Nenhuma narrativa encontrada para remover"
            }
    except Exception as e:
        logger.error(f"Erro ao deletar narrativas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar narrativas: {str(e)}"
        )
    
@router.get("/chroma/campaign/{campaign_id}/full-context", summary="Contexto completo da campanha para retomada")
async def get_full_campaign_context(
    campaign_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store_service),
    current_user_id: str = Depends(get_current_user)
):
    """
    Retorna todo o contexto narrativo da campanha para retomar conversa
    Ordena cronologicamente para reconstruir a história
    """
    try:
        history = vector_store.get_campaign_history(
            campaign_id=campaign_id,
            chapter=None,
            limit=100
        )

        history.sort(key=lambda x: x['metadata'].get('timestamp', ''))
        
        conversation_history = []
        for item in history:
            if item['metadata'].get('message'):
                conversation_history.append({
                    "role": "user",
                    "content": item['metadata']['message'],
                    "timestamp": item['metadata']['timestamp'],
                    "interaction": item['metadata']['interaction_count']
                })

            conversation_history.append({
                "role": "assistant", 
                "content": item['narrative'],
                "timestamp": item['metadata']['timestamp'],
                "interaction": item['metadata']['interaction_count'],
                "chapter": item['metadata']['chapter'],
                "phase": item['metadata']['phase']
            })
        
        logger.info(f"Contexto carregado para campanha {campaign_id}: {len(conversation_history)} mensagens")
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "total_messages": len(conversation_history),
            "conversation_history": conversation_history,
            "last_interaction": history[-1]['metadata']['interaction_count'] if history else 0
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar contexto: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar contexto: {str(e)}"
        )

@router.delete("/chroma/campaign/{campaign_id}/current-only", summary="Limpar apenas campaign_current")
async def clear_current_campaign_only(
    campaign_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store_service),
    current_user_id: str = Depends(get_current_user)
):
    """Remove apenas narrativas da campaign_current, mantém archive e world_lore"""
    try:
        success = vector_store.clear_current_campaign_only(campaign_id)
        if success:
            return {
                "success": True,
                "message": f"Narrativas atuais da campanha {campaign_id} removidas. World lore preservado."
            }
        else:
            return {
                "success": False,
                "message": "Nenhuma narrativa encontrada para remover"
            }
    except Exception as e:
        logger.error(f"Erro ao limpar campaign_current: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao limpar narrativas: {str(e)}"
        )