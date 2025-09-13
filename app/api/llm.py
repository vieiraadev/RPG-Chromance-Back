from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.schemas.llm import (
    LLMChatRequest, 
    LLMChatResponse, 
    CharacterSuggestionRequest,
    LLMHealthCheck
)
from app.services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["LLM"])

def get_llm_service() -> LLMService:
    return LLMService()

@router.post("/chat", response_model=LLMChatResponse, summary="Chat com LLM")
async def chat_with_llm(
    request: LLMChatRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Envia mensagem para a LLM e retorna resposta.
    Pode incluir contexto de personagem se character_id for fornecido.
    """
    try:
        character_context = None
        
        # TODO: Quando integrar com characters, buscar contexto do personagem
        # if request.character_id:
        #     from app.services.character_service import CharacterService
        #     character_service = CharacterService()
        #     character = await character_service.get_by_id(request.character_id)
        #     if character:
        #         character_context = {
        #             "nome": character.nome,
        #             "raca": character.raca,
        #             "classe": character.classe,
        #             "nivel": character.nivel,
        #             "descricao": character.descricao
        #         }
        
        history = []
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.conversation_history
            ]
        result = await llm_service.chat_with_llm(
            message=request.message,
            character_context=character_context,
            conversation_history=history
        )
        
        return LLMChatResponse(**result)
        
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