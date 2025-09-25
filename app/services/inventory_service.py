import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class InventoryService:
    """Serviço para gerenciar inventário e recompensas de capítulos"""
    
    CHAPTER_REWARDS = {
        1: {
            "id": "cubo_sombras",
            "name": "Cubo das Sombras",
            "description": "Relíquia antiga pulsante com energia ancestral",
            "type": "reward",
            "metadata": {
                "power": "Manipulação de Sombras",
                "rarity": "Lendário",
                "effect": "+5 Energia, +3 Inteligência"
            }
        },
        2: {
            "id": "cristal_arcano",
            "name": "Cristal Arcano Puro",
            "description": "Cristal instável com imenso poder arcano",
            "type": "reward",
            "metadata": {
                "power": "Energia Arcana",
                "rarity": "Épico",
                "effect": "+4 Inteligência, +2 Vida"
            }
        },
        3: {
            "id": "cinturao_campeao",
            "name": "Cinturão do Campeão",
            "description": "Troféu conquistado no Coliseu de Neon",
            "type": "reward",
            "metadata": {
                "power": "Força Aprimorada",
                "rarity": "Épico",
                "effect": "+5 Força, +3 Vida"
            }
        }
    }
    
    @classmethod
    def get_chapter_reward(cls, chapter: int) -> Optional[Dict[str, Any]]:
        """Retorna a recompensa definida para o capítulo"""
        return cls.CHAPTER_REWARDS.get(chapter)
    
    @classmethod
    def create_reward_item(cls, chapter: int, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Cria um item de recompensa para o capítulo"""
        reward_template = cls.get_chapter_reward(chapter)
        
        if not reward_template:
            reward_template = {
                "id": f"reward_chapter_{chapter}",
                "name": f"Tesouro do Capítulo {chapter}",
                "description": f"Recompensa obtida ao completar o capítulo {chapter}",
                "type": "reward",
                "metadata": {"rarity": "Raro"}
            }

        reward_item = reward_template.copy()
        reward_item["id"] = f"{reward_item['id']}_{uuid.uuid4().hex[:8]}"
        reward_item["chapter"] = chapter
        reward_item["campaign_id"] = campaign_id
        reward_item["obtained_at"] = datetime.utcnow()
        
        return reward_item
    
    @classmethod
    def detect_reward_in_response(cls, llm_response: str, chapter: int) -> bool:
        """
        Detecta se a recompensa foi entregue na resposta da LLM
        Versão robusta com múltiplos padrões de detecção
        """
        reward = cls.get_chapter_reward(chapter)
        
        if not reward:
            logger.warning(f"Nenhuma recompensa definida para o capítulo {chapter}")
            return False
        
        response_lower = llm_response.lower()
        
        action_words = [
            "obtém", "obteve", "recebe", "recebeu", "conquista", "conquistou",
            "adquire", "adquiriu", "pega", "pegou", "encontra", "encontrou",
            "consegue", "conseguiu", "alcança", "alcançou", "segura", "segurou",
            "toma", "tomou", "coleta", "coletou", "apanha", "apanhou",
            "captura", "capturou", "tem a", "tem o"
        ]

        reward_words = [w.lower() for w in reward["name"].split() if len(w) > 3]
        
        alternative_names = {
            1: ["relíquia perdida", "relíquia", "cubo das sombras", "cubo", "objeto"],
            2: ["cristal arcano", "cristal puro", "cristal", "fragmento arcano"],
            3: ["cinturão do campeão", "cinturão", "troféu", "prêmio"]
        }
        
        completion_phrases = [
            "fim do capítulo",
            "capítulo concluído",
            "missão cumprida",
            "objetivo alcançado",
            "final do capítulo",
            "recompensa final",
            "vitória"
        ]
        
        has_action = any(word in response_lower for word in action_words)
        has_reward_name = any(word in response_lower for word in reward_words)
        has_alternative = any(alt in response_lower for alt in alternative_names.get(chapter, []))
        is_completion = any(phrase in response_lower for phrase in completion_phrases)
        
        logger.debug(f"Detecção de recompensa Capítulo {chapter}:")
        logger.debug(f"  - Has action: {has_action}")
        logger.debug(f"  - Has reward name: {has_reward_name}")
        logger.debug(f"  - Has alternative: {has_alternative}")
        logger.debug(f"  - Is completion: {is_completion}")
        
        detected = (
            (has_action and (has_reward_name or has_alternative)) or
            (is_completion and (has_reward_name or has_alternative))
        )
        
        if detected:
            logger.info(f"Recompensa do capítulo {chapter} detectada!")
        else:
            logger.debug(f"Recompensa do capítulo {chapter} NÃO detectada")
        
        return detected