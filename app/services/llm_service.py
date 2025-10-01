import logging
import json
import re
from typing import Dict, Any, Optional, List
from enum import Enum
import httpx
import asyncio
from app.config import GROQ_API_KEY, LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

class ProgressionPhase(Enum):
    INTRODUCTION = "introduction"
    DEVELOPMENT = "development"    
    RESOLUTION = "resolution"   

class ChapterProgressionManager:
    """Gerencia a progressão narrativa de um capítulo em 10 interações"""
    
    def __init__(self):
        self.max_interactions = 10
        
    def get_current_phase(self, interaction_count: int) -> ProgressionPhase:
        """Determina a fase atual baseada no número de interações"""
        if interaction_count <= 3:
            return ProgressionPhase.INTRODUCTION
        elif interaction_count <= 7:
            return ProgressionPhase.DEVELOPMENT
        else:
            return ProgressionPhase.RESOLUTION
    
    def should_provide_final_reward(self, interaction_count: int) -> bool:
        """Verifica se deve entregar a recompensa final"""
        return interaction_count >= 8
    
    def get_progression_prompt_addition(self, interaction_count: int, chapter: int) -> str:
        """Gera contexto adicional para o prompt baseado na progressão"""
        
        phase = self.get_current_phase(interaction_count)
        
        interactions_in_phase = interaction_count - (
            0 if phase == ProgressionPhase.INTRODUCTION else
            3 if phase == ProgressionPhase.DEVELOPMENT else 7
        )
        
        total_interactions = f"{interaction_count}/10"
        
        prompt_addition = f"""

            PROGRESSÃO DO CAPÍTULO ({total_interactions}):

            FASE ATUAL: {phase.value.upper()}
            INTERAÇÃO NA FASE: {interactions_in_phase + 1}"""

        if phase == ProgressionPhase.INTRODUCTION:
            prompt_addition += """

                INSTRUÇÕES PARA INTRODUÇÃO (1-3 interações):
                - Estabeleça a atmosfera e contexto do capítulo
                - Apresente o ambiente de forma envolvente
                - Introduza elementos de mistério/desafio gradualmente
                - Permita exploração e descoberta inicial
                - Prepare o terreno para os desafios principais"""

        elif phase == ProgressionPhase.DEVELOPMENT:
            prompt_addition += """

                INSTRUÇÕES PARA DESENVOLVIMENTO (4-7 interações):
                - Apresente os desafios principais do capítulo
                - Eleve progressivamente a tensão e dificuldade
                - Desenvolva a narrativa com obstáculos interessantes
                - Permita crescimento e progresso do personagem
                - Construa em direção ao clímax final"""

        else:  
            prompt_addition += """

                INSTRUÇÕES PARA RESOLUÇÃO (8-10 interações):
                - Conduza para o clímax e resolução do capítulo
                - Apresente o desafio/inimigo final se apropriado
                - IMPORTANTE: Nas interações 8-10, prepare a entrega da recompensa final
                - Na interação 9 ou 10, ENTREGUE o item/objetivo principal do capítulo
                - Conclua de forma épica e satisfatória
                - Prepare transição para o próximo capítulo se aplicável"""

        if interaction_count >= 8:
            prompt_addition += f"""

                ATENÇÃO: ZONA DE RECOMPENSA FINAL!
                - Esta é uma das últimas interações do capítulo
                - Se ainda não entregou, DEVE entregar o item/objetivo principal
                - Faça a entrega de forma épica e memorável
                - Conclua a narrativa do capítulo satisfatoriamente"""

        return prompt_addition

class LLMService:
    """Service para integração com LLM usando Groq com sistema de progressão e RAG"""
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1" 
        self.model = LLM_MODEL
        self.progression_manager = ChapterProgressionManager()
        self.vector_store = VectorStoreService()
        
    async def chat_with_llm(
        self, 
        message: str, 
        character_context: Optional[Dict[str, Any]] = None,
        campaign_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[list] = None,
        generate_actions: bool = True,
        max_retries: int = 2,
        interaction_count: int = 1
    ) -> Dict[str, Any]:
        """
        Envia mensagem para a LLM Groq com sistema de progressão narrativa e RAG
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Groq API key não configurada. Configure GROQ_API_KEY no arquivo .env"
                }

            result = await self._make_llm_request(
                message, character_context, campaign_context, 
                conversation_history, generate_actions, use_strict_format=False,
                interaction_count=interaction_count
            )
            
            if not result["success"]:
                return result
                
            llm_response = result["raw_response"]
            logger.info(f"Resposta completa da LLM (Interação {interaction_count}/10): {llm_response}")
            
            contextual_actions = []
            if generate_actions:
                contextual_actions = self._extract_actions_from_response(llm_response)

                progression_actions = self._get_progression_actions(interaction_count, campaign_context)
                if progression_actions:
                    contextual_actions.extend(progression_actions)
                
                if not contextual_actions or self._is_fallback_actions(contextual_actions):
                    logger.info("Primeira tentativa falhou, tentando formato rigoroso...")
                    strict_result = await self._retry_with_strict_format(
                        message, character_context, campaign_context, 
                        conversation_history, interaction_count
                    )
                    
                    if strict_result and strict_result.get("contextual_actions"):
                        contextual_actions = strict_result["contextual_actions"]
                        logger.info("Ações extraídas com sucesso no formato rigoroso")
                
                logger.info(f"Ações finais extraídas: {contextual_actions}")
            
            clean_response = self._clean_response_text(llm_response)

            if campaign_context and character_context:
                try:
                    chapter = campaign_context.get('current_chapter', 1) or 1
                    phase = self.progression_manager.get_current_phase(interaction_count)
                    
                    doc_id = self.vector_store.store_narrative(
                        narrative_text=clean_response,
                        campaign_id=str(campaign_context.get('_id', 'unknown')),
                        character_id=str(character_context.get('_id', 'unknown')),
                        user_id=str(campaign_context.get('user_id', 'unknown')),
                        interaction_count=interaction_count,
                        chapter=int(chapter),
                        phase=phase.value,
                        metadata={
                            "character_name": character_context.get('nome'),
                            "character_class": character_context.get('classe'),
                            "campaign_title": campaign_context.get('title'),
                            "model_used": self.model,
                            "message": message[:100]
                        }
                    )
                    
                    if doc_id:
                        logger.info(f"Narrativa salva no ChromaDB: {doc_id}")
                        
                except Exception as e:
                    logger.error(f"Erro ao salvar no ChromaDB: {e}")
            
            progression_info = self._get_progression_info(interaction_count, campaign_context)
            
            return {
                "success": True,
                "response": clean_response,
                "contextual_actions": contextual_actions,
                "usage": result.get("usage", {}),
                "provider": "Groq",
                "progression": progression_info
            }
                    
        except Exception as e:
            logger.error(f"Erro ao processar Groq LLM: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    async def _get_relevant_context_from_history(
        self,
        message: str,
        campaign_context: Optional[Dict[str, Any]],
        n_results: int = 3
    ) -> str:
        """Busca narrativas relevantes usando RAG"""
        if not campaign_context or not campaign_context.get('_id'):
            return ""
        
        try:
            similar_narratives = self.vector_store.search_similar_narratives(
                query_text=message,
                campaign_id=str(campaign_context.get('_id')),
                chapter=campaign_context.get('current_chapter'),
                n_results=n_results
            )
            
            if not similar_narratives:
                return ""

            context_parts = ["CONTEXTO RELEVANTE (Conhecimento do Mundo):"]
            
            for i, item in enumerate(similar_narratives, 1):
                narrative = item['narrative']
                metadata = item['metadata']
                source = item.get('source', 'unknown')
                
                source_label = "LORE" if source == "lore" else f"Cap {metadata.get('chapter', '?')}"
                
                if len(narrative) > 200:
                    narrative = narrative[:197] + "..."
                
                context_parts.append(
                    f"{i}. [{source_label}] {narrative}"
                )
            
            context_text = "\n".join(context_parts)
            logger.info(f"RAG: Recuperadas {len(similar_narratives)} narrativas relevantes")
            
            return context_text
            
        except Exception as e:
            logger.error(f"Erro ao buscar contexto RAG: {e}")
            return ""
    
    async def _make_llm_request(
        self, message: str, character_context: Optional[Dict[str, Any]], 
        campaign_context: Optional[Dict[str, Any]], conversation_history: Optional[list],
        generate_actions: bool, use_strict_format: bool = False, 
        interaction_count: int = 1
    ) -> Dict[str, Any]:
        """Faz a requisição incluindo progressão e RAG"""
        try:
            rag_context = await self._get_relevant_context_from_history(
                message=message,
                campaign_context=campaign_context,
                n_results=3
            )
            
            system_message = self._build_system_message(
                character_context, campaign_context, generate_actions, 
                use_strict_format, interaction_count, rag_context
            )
            
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
                        "temperature": 0.3 if use_strict_format else LLM_TEMPERATURE
                    },
                    timeout=20.0 
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "raw_response": data["choices"][0]["message"]["content"],
                        "usage": data.get("usage", {})
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
            logger.error(f"Erro na requisição: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    async def _retry_with_strict_format(
        self, message: str, character_context: Optional[Dict[str, Any]], 
        campaign_context: Optional[Dict[str, Any]], conversation_history: Optional[list],
        interaction_count: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Segunda tentativa com formato mais rigoroso"""
        try:
            result = await self._make_llm_request(
                f"Resposta anterior foi inválida. {message}", 
                character_context, campaign_context, conversation_history, 
                generate_actions=True, use_strict_format=True,
                interaction_count=interaction_count
            )
            
            if result["success"]:
                actions = self._extract_actions_from_response(result["raw_response"])
                return {"contextual_actions": actions}
                
        except Exception as e:
            logger.error(f"Erro na segunda tentativa: {e}")
            
        return None
    
    def _is_fallback_actions(self, actions: List[Dict]) -> bool:
        """Verifica se as ações são do tipo fallback (indicando falha na extração)"""
        if not actions:
            return True
            
        fallback_categories = ["fallback", "general", "default"]
        return any(action.get("category") in fallback_categories for action in actions)
    
    def _build_system_message(
        self, character_context: Optional[Dict[str, Any]] = None, 
        campaign_context: Optional[Dict[str, Any]] = None, 
        generate_actions: bool = True, 
        use_strict_format: bool = False,
        interaction_count: int = 1,
        rag_context: str = ""
    ) -> str:
        """Constrói mensagem de sistema com progressão narrativa e RAG"""
        
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
        
        if rag_context:
            base_context += f"""

                {rag_context}

                REGRA CRÍTICA DE MEMÓRIA:
                - O contexto acima mostra APENAS conhecimento geral do mundo (locais, itens, NPCs que EXISTEM)
                - Itens marcados como [LORE] são conhecimento universal do mundo
                - NUNCA invente que o jogador visitou locais, pegou itens ou conheceu NPCs a menos que esteja EXPLICITAMENTE no histórico recente desta conversa
                - Você pode dizer "existe uma Catedral", mas NÃO "você esteve na Catedral" (a menos que tenha acontecido nesta campanha)
                - Você pode dizer "o Cubo das Sombras é uma relíquia poderosa", mas NÃO "você pegou o Cubo" (a menos que tenha acontecido nesta campanha)
                - Se o jogador perguntar sobre algo do passado, responda com conhecimento geral, não com memórias inventadas
                - MANTENHA CONSISTÊNCIA: Use o contexto para saber o que EXISTE, mas NÃO para inventar experiências do jogador"""

        if campaign_context:
            campaign_info = f"""

                CAMPANHA ATIVA: {campaign_context.get('title', 'Campanha Desconhecida')}"""
            
            chapter = campaign_context.get('current_chapter', 1)
            
            if not chapter or chapter <= 0:
                chapter = campaign_context.get('chapter', 1)
            
            try:
                chapter = int(chapter)
            except (ValueError, TypeError):
                chapter = 1
            
            campaign_info += f"""
                CAPÍTULO ATUAL: {chapter}"""
            
            if chapter == 1:
                campaign_info += """

                    CONTEXTO DO CAPÍTULO 1 - "O Cubo das Sombras":
                    - Localização: Catedral em ruínas nas profundezas da cidade
                    - Objetivo: Encontrar a Relíquia Perdida (cubo pulsante de energia ancestral)
                    - Atmosfera: Sombria, antiga, misteriosa
                    - Perigos: Armadilhas ocultas, corrupção energética, guardas sombrios
                    - Elementos: Arquitetura gótica, energias sobrenaturais, tecnologia antiga
                    - Crie situações relacionadas a exploração de ruínas, armadilhas mágicas, e a busca pelo cubo místico."""
                
            elif chapter == 2:
                campaign_info += """

                    CONTEXTO DO CAPÍTULO 2 - "Laboratório de Cristais Arcanos":
                    - Localização: Laboratório oculto nas profundezas da fortaleza inimiga
                    - Objetivo: Investigar experimentos proibidos com energia arcana
                    - Atmosfera: Científica, perigosa, experimental
                    - Perigos: Experimentos instáveis, cristais explosivos, cientistas loucos
                    - Elementos: Tecnologia avançada, cristais mágicos, energia instável
                    - Crie situações relacionadas a laboratórios high-tech, experimentos perigosos, e cristais com poderes arcanos."""
                
            elif chapter == 3: 
                campaign_info += """

                    CONTEXTO DO CAPÍTULO 3 - "Coliseu de Neon":
                    - Localização: Coração da cidade subterrânea, beco entre prédios decadentes
                    - Objetivo: Sobreviver aos combates no coliseu underground
                    - Atmosfera: Urbana, violenta, espetacular
                    - Perigos: Combatentes letais, apostas perigosas, gangues urbanas
                    - Elementos: Luzes de neon, multidões, arena de combate, ambiente cyberpunk urbano
                    - Crie situações relacionadas a combates de arena, apostas ilegais, e a vida nas ruas cyberpunk."""
            
            else:
                campaign_info += f"""

                    CONTEXTO DO CAPÍTULO {chapter} - "Aventura Cyberpunk":
                    - Localização: Ambiente cyberpunk apropriado para o capítulo
                    - Objetivo: Missão desafiadora no universo Chromance
                    - Atmosfera: Cyberpunk, tecnológica, misteriosa
                    - Perigos: Ameaças tecnológicas e místicas apropriadas
                    - Elementos: Tecnologia avançada, magia arcana, ambiente urbano
                    - Crie situações interessantes e envolventes para este capítulo."""
            
            progression_context = self.progression_manager.get_progression_prompt_addition(
                interaction_count, chapter
            )
            campaign_info += progression_context
            
            base_context += campaign_info
        
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
            if use_strict_format:
                actions_instruction = """

                FORMATO CRÍTICO - SIGA EXATAMENTE:

                1. Escreva sua narrativa (máximo 120 palavras)
                2. Adicione uma linha vazia
                3. Escreva EXATAMENTE: [ACOES]
                4. Próxima linha: JSON com 3 ações

                EXEMPLO OBRIGATÓRIO:
                Sua narrativa aqui...

                [ACOES]
                {"actions":[{"name":"Ação A","description":"Descrição A"},{"name":"Ação B","description":"Descrição B"},{"name":"Ação C","description":"Descrição C"}]}

                REGRAS OBRIGATÓRIAS:
                - JSON em UMA linha só
                - Exatamente 3 ações
                - Apenas campos "name" e "description"
                - Nomes curtos (máximo 30 chars)
                - Descrições curtas (máximo 60 chars)
                - NÃO adicione nada após o JSON"""
                
            else:
                actions_instruction = """

                    FORMATO DE RESPOSTA:
                    1. Escreva sua narrativa (máximo 120 palavras)
                    2. Linha em branco
                    3. Adicione: [ACOES]
                    4. JSON das ações:

                    {"actions":[{"name":"Nome da Ação 1","description":"Descrição da ação 1"},{"name":"Nome da Ação 2","description":"Descrição da ação 2"},{"name":"Nome da Ação 3","description":"Descrição da ação 3"}]}

                    - JSON em linha única
                    - Exatamente 3 ações
                    - Apenas campos "name" e "description" """
            
            base_context += actions_instruction
            
        return base_context
    
    def _extract_actions_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Extrai ações contextuais da resposta da LLM"""
        try:
            logger.debug(f"Tentando extrair ações de: {response[:200]}...")
            
            actions = self._extract_strict_actions_pattern(response)
            if actions:
                logger.info("✓ Ações extraídas com padrão rigoroso")
                return actions
            
            actions = self._extract_any_valid_json(response)
            if actions:
                logger.info("✓ Ações extraídas de JSON encontrado")
                return actions
            
            actions = self._extract_flexible_actions(response)
            if actions:
                logger.info("✓ Ações extraídas com regex flexível")
                return actions
            
            logger.info("→ Usando fallback inteligente")
            return self._generate_smart_fallback_actions(response)
            
        except Exception as e:
            logger.error(f"Erro crítico na extração: {e}")
            return self._generate_basic_fallback_actions()
    
    def _extract_strict_actions_pattern(self, response: str) -> List[Dict[str, Any]]:
        """Extração rigorosa do padrão [ACOES]"""
        try:
            pattern = r'\[A[CÇ][OÕ]ES?\]\s*\n?\s*(\{"actions":\s*\[.*?\]\s*\})'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            
            if match:
                json_text = match.group(1).strip()
                logger.debug(f"JSON rigoroso encontrado: {json_text}")
                
                data = json.loads(json_text)
                if isinstance(data.get("actions"), list) and len(data["actions"]) > 0:
                    return self._format_actions(data["actions"])
                    
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Erro no padrão rigoroso: {e}")
            
        return []
    
    def _extract_any_valid_json(self, response: str) -> List[Dict[str, Any]]:
        """Busca qualquer JSON válido com ações"""
        try:
            json_patterns = [
                r'\{"actions":\s*\[.*?\]\}',
                r'\{[^{}]*"actions"\s*:\s*\[[^\]]*\][^{}]*\}',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
                
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data.get("actions"), list) and len(data["actions"]) > 0:
                            logger.debug(f"JSON válido encontrado: {match[:100]}...")
                            return self._format_actions(data["actions"])
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.debug(f"Erro na busca de JSON: {e}")
            
        return []
    
    def _extract_flexible_actions(self, response: str) -> List[Dict[str, Any]]:
        """Extração flexível usando regex para campos individuais"""
        try:
            actions = []
            
            pattern = r'"name"\s*:\s*"([^"]{1,50})"\s*[,}][^}]*"description"\s*:\s*"([^"]{1,100})"'
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            
            for i, (name, description) in enumerate(matches[:3]):
                if name.strip() and description.strip():
                    actions.append({
                        "id": f"extracted_{i+1}",
                        "name": name.strip(),
                        "description": description.strip(),
                        "priority": 3 - i,
                        "category": "extracted"
                    })
            
            return actions if len(actions) >= 2 else []
            
        except Exception as e:
            logger.debug(f"Erro na extração flexível: {e}")
            
        return []
    
    def _format_actions(self, raw_actions: List[Dict]) -> List[Dict[str, Any]]:
        """Formata as ações extraídas"""
        formatted_actions = []
        
        for i, action in enumerate(raw_actions[:3]):
            try:
                name = str(action.get("name", f"Ação {i+1}")).strip()
                description = str(action.get("description", "Sem descrição")).strip()
                
                if len(name) > 50:
                    name = name[:47] + "..."
                if len(description) > 100:
                    description = description[:97] + "..."
                
                if name and description:
                    formatted_actions.append({
                        "id": f"action_{i+1}",
                        "name": name,
                        "description": description,
                        "priority": 4 - i,
                        "category": "contextual"
                    })
                    
            except Exception as e:
                logger.debug(f"Erro ao formatar ação {i}: {e}")
                continue
        
        return formatted_actions
    
    def _generate_smart_fallback_actions(self, response: str) -> List[Dict[str, Any]]:
        """Fallback inteligente baseado no contexto da resposta"""
        actions = []
        response_lower = response.lower()
        
        context_maps = {
            "exploração": {
                "keywords": ["catedral", "ruína", "porta", "entrada", "corredor", "sala", "arquitetura"],
                "actions": [
                    {"name": "Examinar Detalhes", "description": "Investigar elementos do ambiente"},
                    {"name": "Avançar Cautelosamente", "description": "Prosseguir com cuidado"},
                    {"name": "Procurar Pistas", "description": "Buscar sinais ou evidências"}
                ]
            },
            "magia": {
                "keywords": ["energia", "arcano", "magia", "símbolo", "poder", "corrupção"],
                "actions": [
                    {"name": "Analisar Energia", "description": "Estudar as forças mágicas"},
                    {"name": "Canalizar Poder", "description": "Focar energia arcana"},
                    {"name": "Criar Proteção", "description": "Estabelecer defesas mágicas"}
                ]
            },
            "tecnologia": {
                "keywords": ["sistema", "computador", "hackear", "rede", "código", "terminal"],
                "actions": [
                    {"name": "Hackear Sistema", "description": "Quebrar segurança digital"},
                    {"name": "Analisar Código", "description": "Estudar programação"},
                    {"name": "Bypass Manual", "description": "Contornar por hardware"}
                ]
            },
            "combate": {
                "keywords": ["inimigo", "guarda", "perigo", "ameaça", "luta", "ataque"],
                "actions": [
                    {"name": "Preparar Combate", "description": "Entrar em posição de luta"},
                    {"name": "Estratégia Furtiva", "description": "Aproximação sigilosa"},
                    {"name": "Procurar Cobertura", "description": "Buscar proteção"}
                ]
            }
        }
        
        best_context = None
        max_matches = 0
        
        for context_name, context_data in context_maps.items():
            matches = sum(1 for keyword in context_data["keywords"] if keyword in response_lower)
            if matches > max_matches:
                max_matches = matches
                best_context = context_data
        
        if best_context and max_matches > 0:
            base_actions = best_context["actions"]
        else:
            base_actions = [
                {"name": "Observar", "description": "Examinar o ambiente atual"},
                {"name": "Prosseguir", "description": "Continuar a aventura"},
                {"name": "Aguardar", "description": "Esperar por mais informações"}
            ]
        
        for i, action_data in enumerate(base_actions[:3]):
            actions.append({
                "id": f"smart_fallback_{i+1}",
                "name": action_data["name"],
                "description": action_data["description"],
                "priority": 3 - i,
                "category": "smart_fallback"
            })
        
        return actions
    
    def _generate_basic_fallback_actions(self) -> List[Dict[str, Any]]:
        """Fallback básico de emergência"""
        return [
            {
                "id": "basic_1",
                "name": "Continuar",
                "description": "Prosseguir com a história",
                "priority": 2,
                "category": "basic_fallback"
            },
            {
                "id": "basic_2", 
                "name": "Examinar",
                "description": "Observar o ambiente",
                "priority": 1,
                "category": "basic_fallback"
            },
            {
                "id": "basic_3",
                "name": "Aguardar",
                "description": "Esperar mais informações",
                "priority": 1,
                "category": "basic_fallback"
            }
        ]
    
    def _clean_response_text(self, response: str) -> str:
        """Remove blocos de ações da resposta principal"""
        clean_text = re.sub(r'\[A[CÇ][OÕ]ES?\].*$', '', response, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'\{[^{}]*"actions"[^}]*\}', '', clean_text, flags=re.DOTALL)
        clean_text = re.sub(r'\{[^{}]*"name"[^}]*\}', '', clean_text, flags=re.DOTALL)
        clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text)
        clean_text = clean_text.strip()
        
        return clean_text

    def _get_progression_actions(self, interaction_count: int, campaign_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Gera ações específicas baseadas na progressão"""
        if not campaign_context:
            return []
        
        chapter = campaign_context.get('current_chapter', 1) or 1
        phase = self.progression_manager.get_current_phase(interaction_count)
        
        progression_actions = []
        
        if phase == ProgressionPhase.INTRODUCTION:
            progression_actions = [
                {
                    "id": f"intro_explore_{interaction_count}",
                    "name": "Explorar Ambiente",
                    "description": "Investigar detalhadamente o cenário",
                    "priority": 4,
                    "category": "progression"
                }
            ]
        
        elif phase == ProgressionPhase.DEVELOPMENT:
            progression_actions = [
                {
                    "id": f"dev_advance_{interaction_count}",
                    "name": "Avançar no Objetivo",
                    "description": "Progredir em direção ao objetivo principal",
                    "priority": 5,
                    "category": "progression"
                }
            ]
        
        elif phase == ProgressionPhase.RESOLUTION:
            if interaction_count >= 8:
                progression_actions = [
                    {
                        "id": f"final_objective_{interaction_count}",
                        "name": "Buscar Recompensa Final",
                        "description": "Tentar obter o item principal do capítulo",
                        "priority": 5,
                        "category": "progression"
                    }
                ]
        
        return progression_actions
    
    def _get_progression_info(self, interaction_count: int, campaign_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Retorna informações sobre a progressão atual"""
        chapter = campaign_context.get('current_chapter', 1) if campaign_context else 1
        phase = self.progression_manager.get_current_phase(interaction_count)
        
        return {
            "interaction_count": interaction_count,
            "max_interactions": self.progression_manager.max_interactions,
            "current_phase": phase.value,
            "chapter": chapter,
            "should_provide_reward": self.progression_manager.should_provide_final_reward(interaction_count),
            "progress_percentage": min((interaction_count / self.progression_manager.max_interactions) * 100, 100)
        }
    
    async def process_reward_delivery(
        self,
        llm_response: str,
        interaction_count: int,
        chapter: int,
        campaign_id: str,
        character_repo,
        character_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Processa entrega de recompensa se detectada"""
        from app.services.inventory_service import InventoryService

        if interaction_count < 8:
            return None

        if InventoryService.detect_reward_in_response(llm_response, chapter):
            logger.info(f"Recompensa detectada no capítulo {chapter}!")

            reward_item = InventoryService.create_reward_item(chapter, campaign_id)

            updated_character = await character_repo.add_item_to_inventory(
                character_id=character_id,
                item=reward_item,
                user_id=user_id
            )
            
            if updated_character:
                logger.info(f"'{reward_item['name']}' adicionado ao inventário!")
                return reward_item
            else:
                logger.error("Falha ao adicionar recompensa ao inventário")
        
        return None
    
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