import logging
import json
import re
from typing import Dict, Any, Optional, List
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
        generate_actions: bool = True,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Envia mensagem para a LLM Groq e retorna resposta com ações contextuais
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Groq API key não configurada. Configure GROQ_API_KEY no arquivo .env"
                }
            
            system_message = self._build_system_message(character_context, generate_actions)
            
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
                        "max_tokens": min(LLM_MAX_TOKENS, 1200), 
                        "temperature": LLM_TEMPERATURE
                    },
                    timeout=20.0 
                )
                
                if response.status_code == 200:
                    data = response.json()
                    llm_response = data["choices"][0]["message"]["content"]
                    
                    logger.info(f"Resposta completa da LLM: {llm_response}")
                    
                    contextual_actions = []
                    if generate_actions:
                        contextual_actions = self._extract_actions_from_response(llm_response)
                        logger.info(f"Ações extraídas: {contextual_actions}")

                    clean_response = self._clean_response_text(llm_response)
                    
                    return {
                        "success": True,
                        "response": clean_response,
                        "contextual_actions": contextual_actions,
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
    
    def _build_system_message(self, character_context: Optional[Dict[str, Any]] = None, generate_actions: bool = True) -> str:
        """Constrói a mensagem de sistema com contexto do RPG"""
        
        base_context = """Você é um Mestre de RPG no universo Chromance, um mundo cyberpunk.

                        MUNDO:
                        - Corporações controlam tudo
                        - Hackers e netrunners
                        - Tecnologia + magia
                        - Neon e atmosfera dark

                        SEU PAPEL:
                        - Seja criativo e envolvente
                        - Mantenha tom cyberpunk
                        - Responda em português
                        - Máximo 120 palavras para a narrativa
                        - Crie situações interessantes"""
        
        if character_context:
            atributos_info = ""
            if character_context.get('atributos'):
                attrs = character_context['atributos']
                atributos_info = f"""
                - Atributos: Vida {attrs.get('vida', 20)}/20, Energia {attrs.get('energia', 20)}/20, Força {attrs.get('forca', 10)}/20, Inteligência {attrs.get('inteligencia', 10)}/20"""
            
            char_info = f"""

                        PERSONAGEM ATIVO:
                        - Nome: {character_context.get('nome', 'Anônimo')}
                        - Raça: {character_context.get('raca', 'Humano')}
                        - Classe: {character_context.get('classe', 'Aventureiro')}{atributos_info}
                        - Descrição: {character_context.get('descricao', 'Sem descrição')}

                        IMPORTANTE: Use estas informações do personagem para personalizar suas respostas. Considere a classe, raça e atributos nas situações que criar."""
            base_context += char_info
        
        if generate_actions:
            actions_instruction = """

                        AÇÕES CONTEXTUAIS:
                        Após sua narrativa, adicione exatamente 3 ações no formato:

                        [AÇÕES]
                        {"actions":[{"name":"Ação 1","description":"Descrição da ação 1"},{"name":"Ação 2","description":"Descrição da ação 2"},{"name":"Ação 3","description":"Descrição da ação 3"}]}

                        IMPORTANTE: Apenas name e description. JSON em linha única."""
            base_context += actions_instruction
            
        return base_context
    
    def _extract_actions_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Extrai ações contextuais da resposta da LLM"""
        try:
            pattern = r'\[AÇÕES\]\s*(.*?)(?:\s*$|\n|$)'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            
            if not match:
                logger.info("Nenhum bloco [AÇÕES] encontrado")
                return self._generate_fallback_actions(response)
            
            json_block = match.group(1).strip()
            logger.info(f"Bloco JSON bruto: {json_block[:200]}...")
            
            try:
                simple_pattern = r'"name"\s*:\s*"([^"]*)"[^}]*"description"\s*:\s*"([^"]*)"'
                matches = re.findall(simple_pattern, json_block, re.DOTALL)
                
                if matches:
                    contextual_actions = []
                    fixed_icons = ['fas fa-play', 'fas fa-play', 'fas fa-play']
                    default_categories = ['general', 'general', 'general']
                    
                    for i, (name, description) in enumerate(matches[:3]):
                        contextual_actions.append({
                            "id": f"action_{i+1}",
                            "name": name.strip()[:50],
                            "description": description.strip()[:100],
                            "priority": 3 - i, 
                            "category": "general"
                        })
                    
                    if contextual_actions:
                        logger.info(f"Ações extraídas: {len(contextual_actions)}")
                        return contextual_actions
                        
            except Exception as e:
                logger.warning(f"Extração falhou: {e}")
                
        except Exception as e:
            logger.warning(f"Erro geral ao extrair ações: {e}")
            
        logger.info("Usando sistema fallback para gerar ações")
        return self._generate_fallback_actions(response)
    
    def _generate_fallback_actions(self, response: str) -> List[Dict[str, Any]]:
        """Gera ações de fallback baseadas no contexto da resposta"""
        actions = []
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['guarda', 'inimigo', 'ameaça', 'perigo']):
            actions.extend([
                {
                    "id": "prepare_combat",
                    "name": "Preparar Combate",
                    "description": "Entrar em posição de luta",
                    "priority": 4,
                    "category": "general"
                },
                {
                    "id": "hide",
                    "name": "Se Esconder",
                    "description": "Procurar cobertura",
                    "priority": 3,
                    "category": "general"
                }
            ])
        
        if any(word in response_lower for word in ['porta', 'entrada', 'saída']):
            actions.append({
                "id": "approach_door",
                "name": "Aproximar da Porta",
                "description": "Investigar a entrada",
                "priority": 2,
                "category": "general"
            })
        
        if any(word in response_lower for word in ['hackear', 'sistema', 'computador', 'terminal']):
            actions.append({
                "id": "hack_system",
                "name": "Hackear Sistema",
                "description": "Tentar quebrar a segurança",
                "priority": 3,
                "category": "general"
            })
        
        if any(word in response_lower for word in ['conversar', 'falar', 'negociar', 'pessoa']):
            actions.append({
                "id": "talk",
                "name": "Conversar",
                "description": "Iniciar diálogo",
                "priority": 2,
                "category": "general"
            })
        
        if not actions:
            actions = [
                {
                    "id": "examine",
                    "name": "Examinar",
                    "description": "Observar o ambiente",
                    "priority": 1,
                    "category": "general"
                },
                {
                    "id": "continue",
                    "name": "Continuar",
                    "description": "Avançar na história",
                    "priority": 2,
                    "category": "general"
                },
                {
                    "id": "think",
                    "name": "Pensar",
                    "description": "Analisar a situação",
                    "priority": 1,
                    "category": "general"
                }
            ]
        
        return actions[:3]  
    
    def _clean_response_text(self, response: str) -> str:
        """Remove blocos de ações da resposta principal"""
        clean_text = re.sub(r'\[AÇÕES\].*$', '', response, flags=re.DOTALL | re.IGNORECASE)
        return clean_text.strip()
    
    async def generate_character_suggestion(self, partial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera sugestões para criação de personagem"""
        
        prompt = f"Baseado nos dados: {partial_data}\n\nSugira melhorias para um personagem cyberpunk de Chromance. Seja criativo mas coerente."
        
        return await self.chat_with_llm(prompt, generate_actions=False)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Testa a conexão com o Groq"""
        try:
            result = await self.chat_with_llm("teste", max_retries=1, generate_actions=False)
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