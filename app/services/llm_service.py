import logging
from typing import Dict, Any, Optional
import httpx
import asyncio
from app.config import GROQ_API_KEY, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

class LLMService:
    """Service para integração com LLM usando Groq"""
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1" 
        self.model = LLM_MODEL
        
    async def chat_with_llm(
        self, 
        message: str, 
        character_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[list] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Envia mensagem para a LLM Groq e retorna resposta
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Groq API key não configurada. Configure GROQ_API_KEY no arquivo .env"
                }
            
            system_message = self._build_system_message(character_context)
            
            messages = [{"role": "system", "content": system_message}]

            if conversation_history:
                messages.extend(conversation_history[-6:])

            messages.append({"role": "user", "content": message})
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": min(LLM_MAX_TOKENS, 1000), 
                        "temperature": LLM_TEMPERATURE
                    },
                    timeout=20.0 
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response": data["choices"][0]["message"]["content"],
                        "usage": data.get("usage", {}),
                        "provider": "Groq"
                    }
                elif response.status_code == 429:
                    return {
                        "success": False,
                        "error": "Rate limit do Groq atingido. Aguarde alguns segundos e tente novamente."
                    }
                else:
                    logger.error(f"Erro na API Groq: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Erro na API Groq: {response.status_code}"
                    }
                    
        except httpx.TimeoutException:
            logger.error("Timeout na requisição Groq")
            return {
                "success": False,
                "error": "Timeout na requisição. Tente novamente."
            }
        except Exception as e:
            logger.error(f"Erro ao processar Groq LLM: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    def _build_system_message(self, character_context: Optional[Dict[str, Any]] = None) -> str:
        """Constrói a mensagem de sistema com contexto do RPG"""
        
        base_context = """Você é um Mestre de RPG no universo Chromance, um mundo cyberpunk.

                    Mundo:
                    - Corporações controlam tudo
                    - Hackers e netrunners
                    - Tecnologia + magia
                    - Neon e atmosfera dark

                    Seu papel:
                    - Seja criativo e envolvente
                    - Mantenha tom cyberpunk
                    - Responda em português
                    - Máximo 150 palavras
                    - Crie situações interessantes"""
        
        if character_context:
            char_info = f"""

            Personagem:
            - Nome: {character_context.get('nome', 'Anônimo')}
            - Classe: {character_context.get('classe', 'Aventureiro')}
            - Nível: {character_context.get('nivel', 1)}

            Use essas informações."""
            base_context += char_info
            
        return base_context
    
    async def generate_character_suggestion(self, partial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera sugestões para criação de personagem"""
        
        prompt = f"Baseado nos dados: {partial_data}\n\nSugira melhorias para um personagem cyberpunk de Chromance. Seja criativo mas coerente."
        
        return await self.chat_with_llm(prompt)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Testa a conexão com o Groq"""
        try:
            result = await self.chat_with_llm("teste", max_retries=1)
            return {
                "success": result["success"],
                "model": self.model,
                "available": result["success"],
                "provider": "Groq"
            }
        except Exception as e:
            return {
                "success": False,
                "model": self.model,
                "available": False,
                "error": str(e),
                "provider": "Groq"
            }