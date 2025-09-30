from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from pymongo.database import Database
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignCreate, CampaignOut, CampaignUpdate


class CampaignService:
    def __init__(self, db: Database):
        self.db = db
        self.campaigns_collection = db["campaigns"]
        self.progress_collection = db["campaign_progress"]

    async def get_campaigns_with_progress(self, user_id: str = None) -> List[Dict]:
        """Retorna todas as campanhas base com o progresso do usuário mesclado"""
        campaigns = []
        
        cursor = self.campaigns_collection.find({"user_id": None}).sort("chapter", 1)
        
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["id"] = doc["_id"]
            
            if user_id:
                progress = self.progress_collection.find_one({
                    "user_id": user_id,
                    "campaign_id": doc["campaign_id"]
                })
                
                if progress:
                    doc["status"] = progress.get("status", None)
                    doc["active_character_id"] = progress.get("active_character_id", None)
                    doc["active_character_name"] = progress.get("active_character_name", None)
                    doc["current_chapter"] = progress.get("current_chapter", 1)
                    doc["chapters_completed"] = progress.get("chapters_completed", [])
                    doc["started_at"] = progress.get("started_at", None)
                    doc["last_played_at"] = progress.get("last_played_at", None)
                    doc["score"] = progress.get("score", 0)
                    doc["battles_won"] = progress.get("battles_won", 0)
                    doc["battles_lost"] = progress.get("battles_lost", 0)
                else:
                    doc["status"] = None
                    doc["active_character_id"] = None
                    doc["active_character_name"] = None
                    doc["current_chapter"] = 1
                    doc["chapters_completed"] = []
                    doc["started_at"] = None
                    doc["score"] = 0
                    doc["battles_won"] = 0
                    doc["battles_lost"] = 0
            
            campaigns.append(CampaignOut(**doc))
        
        return campaigns

    async def get_campaigns(self, user_id: str = None) -> List[CampaignOut]:
        """Retorna todas as campanhas com progresso do usuário se fornecido"""
        return await self.get_campaigns_with_progress(user_id)

    async def get_campaign_by_id(self, campaign_id: str, user_id: str = None) -> Optional[CampaignOut]:
        """Busca uma campanha específica com progresso do usuário"""
        doc = self.campaigns_collection.find_one({
            "campaign_id": campaign_id,
            "user_id": None 
        })
        
        if not doc:
            return None
        
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        
        if user_id:
            progress = self.progress_collection.find_one({
                "user_id": user_id,
                "campaign_id": campaign_id
            })
            
            if progress:
                doc["status"] = progress.get("status", None)
                doc["active_character_id"] = progress.get("active_character_id", None)
                doc["active_character_name"] = progress.get("active_character_name", None)
                doc["current_chapter"] = progress.get("current_chapter", 1)
                doc["chapters_completed"] = progress.get("chapters_completed", [])
                doc["started_at"] = progress.get("started_at", None)
                doc["score"] = progress.get("score", 0)
        
        return CampaignOut(**doc)

    async def start_campaign(self, campaign_id: str, character_id: str, character_name: str, user_id: str) -> CampaignOut:
        """Inicia uma campanha criando/atualizando o progresso do usuário"""
        
        campaign = self.campaigns_collection.find_one({
            "campaign_id": campaign_id,
            "user_id": None
        })
        
        if not campaign:
            await self.seed_campaigns()
            campaign = self.campaigns_collection.find_one({
                "campaign_id": campaign_id,
                "user_id": None
            })
        
        if not campaign:
            raise ValueError(f"Campanha {campaign_id} não encontrada")
        
        self.progress_collection.update_many(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"status": "cancelled"}}
        )
        
        progress_data = {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "status": "in_progress",
            "active_character_id": character_id,
            "active_character_name": character_name,
            "current_chapter": 1,
            "chapters_completed": [],
            "score": 0,
            "battles_won": 0,
            "battles_lost": 0,
            "items_collected": [],
            "started_at": datetime.now(),
            "last_played_at": datetime.now()
        }
        
        self.progress_collection.update_one(
            {"user_id": user_id, "campaign_id": campaign_id},
            {"$set": progress_data},
            upsert=True
        )
        
        return await self.get_campaign_by_id(campaign_id, user_id)

    async def get_active_campaign(self, user_id: str) -> Optional[CampaignOut]:
        """Retorna a campanha ativa do usuário"""
        progress = self.progress_collection.find_one({
            "user_id": user_id,
            "status": "in_progress"
        })
        
        if not progress:
            return None
        
        return await self.get_campaign_by_id(progress["campaign_id"], user_id)

    async def complete_chapter(self, campaign_id: str, chapter: int, user_id: str) -> Optional[CampaignOut]:
        """Marca um capítulo como completo no progresso do usuário"""
        result = self.progress_collection.update_one(
            {"user_id": user_id, "campaign_id": campaign_id},
            {
                "$addToSet": {"chapters_completed": chapter},
                "$set": {
                    "current_chapter": chapter + 1,
                    "last_played_at": datetime.now()
                }
            }
        )
        
        if result.modified_count:
            return await self.get_campaign_by_id(campaign_id, user_id)
        
        return None

    async def cancel_campaign(self, campaign_id: str, user_id: str) -> bool:
        """Cancela uma campanha ativa do usuário"""
        result = self.progress_collection.update_one(
            {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "status": "in_progress"
            },
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.now()
                }
            }
        )
        return result.modified_count > 0

    async def update_campaign(self, campaign_id: str, update_data: any, user_id: str = None) -> Optional[CampaignOut]:
        """Atualiza dados de uma campanha (compatibilidade com API)"""
        if not user_id:
            return None
            
        update_dict = {}
        if hasattr(update_data, 'status'):
            update_dict['status'] = update_data.status
        if hasattr(update_data, 'cancelled_at'):
            update_dict['cancelled_at'] = update_data.cancelled_at
            
        if update_dict:
            result = self.progress_collection.update_one(
                {"user_id": user_id, "campaign_id": campaign_id},
                {"$set": update_dict},
                upsert=True
            )
            
            if result.modified_count or result.upserted_id:
                return await self.get_campaign_by_id(campaign_id, user_id)
        
        return None

    async def update_battle_stats(self, campaign_id: str, user_id: str, won: bool) -> bool:
        """Atualiza estatísticas de batalha"""
        field = "battles_won" if won else "battles_lost"
        result = self.progress_collection.update_one(
            {"user_id": user_id, "campaign_id": campaign_id},
            {
                "$inc": {field: 1, "score": 10 if won else -5},
                "$set": {"last_played_at": datetime.now()}
            }
        )
        return result.modified_count > 0

    async def seed_campaigns(self) -> List[CampaignOut]:
        """Cria as campanhas base (globais) no banco"""
        
        self.campaigns_collection.delete_many({"user_id": None})
        
        campaigns_data = [
            {
                "campaign_id": "arena-sombras",
                "title": "Capítulo 1 : O Cubo das Sombras",
                "chapter": 1,
                "description": "Nas profundezas de uma catedral em ruínas, o guerreiro sombrio encontra a Relíquia Perdida — um cubo pulsante de energia ancestral.",
                "full_description": "Nas profundezas de uma catedral em ruínas, o guerreiro sombrio encontra a Relíquia Perdida — um cubo pulsante de energia ancestral. Para conquistá-lo, deve enfrentar as armadilhas ocultas que protegem seu poder e resistir à corrupção que emana da própria relíquia.",
                "image": "./assets/images/campaign-thumb1.jpg",
                "thumbnail": "./assets/images/campaign-thumb1.jpg",
                "rewards": [
                    {"type": "artifact", "name": "Cubo das Sombras", "icon": "cubo_sombras"}
                ],
                "is_locked": False,
                "user_id": None, 
                "chapters_completed": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "campaign_id": "laboratorio-cristais",
                "title": "Capítulo 2 : Laboratório de Cristais Arcanos",
                "chapter": 2,
                "description": "Em um laboratório oculto nas profundezas da fortaleza inimiga, um cientista obcecado conduz experiências proibidas.",
                "full_description": "Em um laboratório oculto nas profundezas da fortaleza inimiga, um cientista obcecado conduz experiências proibidas com fragmentos de energia arcana.",
                "image": "./assets/images/campaign-thumb2.jpg",
                "thumbnail": "./assets/images/campaign-thumb2.jpg",
                "rewards": [
                    {"type": "crystal", "name": "Cristal Arcano Puro", "icon": "cristal_arcano"}
                ],
                "is_locked": False,
                "user_id": None,
                "chapters_completed": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "campaign_id": "coliseu-de-neon",
                "title": "Capítulo 3 : Coliseu de Neon",
                "chapter": 3,
                "description": "No coração da cidade subterrânea, em um beco cercado por prédios decadentes.",
                "full_description": "No coração da cidade subterrânea, em um beco cercado por prédios decadentes e iluminado apenas por letreiros de neon.",
                "image": "./assets/images/campaign-image3.jpg",
                "thumbnail": "./assets/images/campaign-image3.jpg",
                "rewards": [
                    {"type": "belt", "name": "Cinturão do Campeão", "icon": "cinturao_campeao"}
                ],
                "is_locked": False,
                "user_id": None,
                "chapters_completed": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        result = self.campaigns_collection.insert_many(campaigns_data)
        print(f"✓ {len(result.inserted_ids)} campanhas base criadas!")
        
        return await self.get_campaigns_with_progress(None)