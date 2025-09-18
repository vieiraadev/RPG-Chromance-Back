from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """Mensagem de chat"""
    role: str = Field(..., description="Papel (user, assistant, system)")
    content: str = Field(..., description="Conteúdo da mensagem")

class ContextualAction(BaseModel):
    """Ação contextual sugerida pela LLM"""
    id: str = Field(..., description="ID único da ação")
    name: str = Field(..., description="Nome da ação")
    description: str = Field(..., description="Descrição da ação")
    priority: int = Field(default=1, description="Prioridade (1-5, sendo 5 mais importante)")
    category: str = Field(default="general", description="Categoria da ação")

class LLMChatRequest(BaseModel):
    """Request para chat com LLM"""
    message: str = Field(..., description="Mensagem do usuário")
    character_id: Optional[str] = Field(None, description="ID do personagem (opcional)")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Histórico da conversa"
    )
    generate_actions: bool = Field(default=True, description="Se deve gerar ações contextuais")

class LLMChatResponse(BaseModel):
    """Response do chat com LLM"""
    success: bool = Field(..., description="Se a requisição foi bem-sucedida")
    response: Optional[str] = Field(None, description="Resposta da LLM")
    contextual_actions: Optional[List[ContextualAction]] = Field(
        default=[],
        description="Ações contextuais sugeridas"
    )
    error: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    usage: Optional[Dict[str, Any]] = Field(None, description="Informações de uso da API")

class CharacterSuggestionRequest(BaseModel):
    """Request para sugestão de personagem"""
    partial_data: Dict[str, Any] = Field(..., description="Dados parciais do personagem")

class StoryContinuationRequest(BaseModel):
    """Request para continuação de história"""
    current_situation: str = Field(..., description="Situação atual da narrativa")
    character_id: str = Field(..., description="ID do personagem")

class LLMHealthCheck(BaseModel):
    """Health check da LLM"""
    status: str = Field(..., description="Status da LLM")
    model: str = Field(..., description="Modelo utilizado")
    available: bool = Field(..., description="Se está disponível")