from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pymongo.database import Database
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel

from app.core.database import get_database

router = APIRouter(prefix="/api/campaigns", tags=["Campanhas"])


class CampaignStart(BaseModel):
    character_id: str
    campaign_id: str


def serialize_campaign(doc):
    """Converte ObjectId para string e limpa o documento"""
    if doc:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        doc["campaign_id"] = doc.get("campaign_id", doc.get("id", ""))
        return doc
    return None


@router.get("/")
async def get_campaigns(db: Database = Depends(get_database)):
    """Retorna todas as campanhas disponíveis com status de ocupação"""
    campaigns_collection = db["campaigns"]
    characters_collection = db["characters"]
    
    campaigns = []
    for doc in campaigns_collection.find().sort("chapter", 1):
        serialized_campaign = serialize_campaign(doc)
        if serialized_campaign:
            if doc.get("active_character_id"):
                character = characters_collection.find_one({"_id": ObjectId(doc["active_character_id"])})
                serialized_campaign["active_character"] = {
                    "id": doc["active_character_id"],
                    "name": character["name"] if character else "Personagem desconhecido"
                }
            
            campaigns.append(serialized_campaign)
    
    return {
        "campaigns": campaigns,
        "total": len(campaigns)
    }


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str, db: Database = Depends(get_database)):
    """Retorna uma campanha específica pelo ID"""
    campaigns_collection = db["campaigns"]
    
    campaign = campaigns_collection.find_one({"campaign_id": campaign_id})
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campanha {campaign_id} não encontrada"
        )
    
    return serialize_campaign(campaign)


@router.post("/start")
async def start_campaign(
    data: CampaignStart, 
    db: Database = Depends(get_database)
):
    """Inicia uma campanha com um personagem"""
    campaigns_collection = db["campaigns"]
    characters_collection = db["characters"]
    
    try:
        character_object_id = ObjectId(data.character_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID do personagem inválido"
        )
    
    character = characters_collection.find_one({"_id": character_object_id})
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personagem não encontrado"
        )

    active_campaign = campaigns_collection.find_one({"status": "in_progress"})
    
    if active_campaign:
        active_char = characters_collection.find_one({"_id": ObjectId(active_campaign["active_character_id"])})
        active_char_name = active_char["name"] if active_char else "Personagem desconhecido"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma campanha em andamento com {active_char_name} em '{active_campaign['title']}'. Finalize-a primeiro ou continue jogando."
        )
    
    campaign = campaigns_collection.find_one({"campaign_id": data.campaign_id})
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    result = campaigns_collection.update_one(
        {"campaign_id": data.campaign_id},
        {
            "$set": {
                "status": "in_progress",
                "active_character_id": data.character_id,
                "active_character_name": character["name"],
                "current_chapter": 1,
                "chapters_completed": [],
                "started_at": datetime.now(),
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao iniciar campanha"
        )
    
    return {
        "message": f"Campanha '{campaign['title']}' iniciada com {character['name']}!",
        "campaign_id": data.campaign_id,
        "character_name": character["name"],
        "current_chapter": 1
    }


@router.put("/{campaign_id}/complete-chapter")
async def complete_chapter(
    campaign_id: str,
    chapter: int,
    db: Database = Depends(get_database)
):
    """Completa um capítulo da campanha ativa"""
    campaigns_collection = db["campaigns"]
    
    campaign = campaigns_collection.find_one({"campaign_id": campaign_id, "status": "in_progress"})
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada ou não está ativa"
        )

    chapters_completed = campaign.get("chapters_completed", [])
    if chapter not in chapters_completed:
        chapters_completed.append(chapter)
    
    if chapter >= 3:
        update_data = {
            "chapters_completed": chapters_completed,
            "current_chapter": 3,
            "status": "completed",
            "active_character_id": None,
            "active_character_name": None,
            "completed_at": datetime.now(),
            "updated_at": datetime.now()
        }
        message = f"Parabéns! Campanha '{campaign['title']}' foi completada por {campaign['active_character_name']}! Todos os personagens estão livres para iniciar novas aventuras."
    else:
        update_data = {
            "chapters_completed": chapters_completed,
            "current_chapter": min(chapter + 1, 3),
            "updated_at": datetime.now()
        }
        message = f"Capítulo {chapter} completado por {campaign['active_character_name']}! Continue para o capítulo {min(chapter + 1, 3)}."
    
    result = campaigns_collection.update_one(
        {"campaign_id": campaign_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao completar capítulo"
        )
    
    return {
        "message": message,
        "chapter_completed": chapter,
        "campaign_freed": chapter >= 3,
        "current_chapter": update_data.get("current_chapter", 3)
    }


@router.delete("/{campaign_id}/cancel")
async def cancel_campaign(
    campaign_id: str,
    db: Database = Depends(get_database)
):
    """Cancela/encerra uma campanha ativa"""
    campaigns_collection = db["campaigns"]
    
    campaign = campaigns_collection.find_one({"campaign_id": campaign_id, "status": "in_progress"})
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada ou não está ativa"
        )

    result = campaigns_collection.update_one(
        {"campaign_id": campaign_id},
        {
            "$set": {
                "status": "cancelled",
                "active_character_id": None,
                "active_character_name": None,
                "cancelled_at": datetime.now(),
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao cancelar campanha"
        )
    
    return {
        "message": f"Campanha '{campaign['title']}' foi cancelada. Todos os personagens estão livres para iniciar novas aventuras!",
        "campaign_freed": True
    }


@router.get("/active/status")
async def get_active_campaign_status(db: Database = Depends(get_database)):
    """Retorna o status da campanha ativa (se houver)"""
    campaigns_collection = db["campaigns"]
    characters_collection = db["characters"]
    
    active_campaign = campaigns_collection.find_one({"status": "in_progress"})
    
    if not active_campaign:
        return {
            "has_active_campaign": False,
            "active_campaign": None
        }
    
    character = None
    if active_campaign.get("active_character_id"):
        character = characters_collection.find_one({"_id": ObjectId(active_campaign["active_character_id"])})
    
    return {
        "has_active_campaign": True,
        "active_campaign": {
            "campaign_id": active_campaign["campaign_id"],
            "title": active_campaign["title"],
            "current_chapter": active_campaign.get("current_chapter", 1),
            "chapters_completed": active_campaign.get("chapters_completed", []),
            "character": {
                "id": active_campaign.get("active_character_id"),
                "name": character["name"] if character else active_campaign.get("active_character_name", "Desconhecido")
            }
        }
    }


@router.post("/seed")
async def seed_campaigns(db: Database = Depends(get_database)):
    """Popula o banco com as campanhas, resetando campos de controle"""
    campaigns_collection = db["campaigns"]
    
    campaigns_collection.delete_many({})
    
    campaigns_data = [
        {
            "campaign_id": "arena-sombras",
            "title": "Capítulo 1 : O Cubo das Sombras",
            "chapter": 1,
            "description": "Nas profundezas de uma catedral em ruínas, o guerreiro sombrio encontra a Relíquia Perdida — um cubo pulsante de energia ancestral.",
            "full_description": "Nas profundezas de uma catedral em ruínas, o guerreiro sombrio encontra a Relíquia Perdida — um cubo pulsante de energia ancestral. Para conquistá-lo, deve enfrentar as armadilhas ocultas que protegem seu poder e resistir à corrupção que emana da própria relíquia. Cada passo ecoa no salão silencioso, enquanto a luz azul da espada e do artefato guia seu caminho através da escuridão. O destino do mundo depende de sua escolha: dominar o cubo ou ser consumido por ele.",
            "image": "./assets/images/campaign-thumb1.jpg",
            "thumbnail": "./assets/images/campaign-thumb1.jpg",
            "rewards": [
                {"type": "weapon", "name": "Lâmina Cybernética", "icon": "sword"},
                {"type": "armor", "name": "Escudo Neural", "icon": "shield"},
                {"type": "health", "name": "Vida +100", "icon": "heart"},
                {"type": "tech", "name": "Chip de Combate", "icon": "chip"}
            ],
            "is_locked": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": None,
            "active_character_id": None,
            "active_character_name": None,
            "current_chapter": None,
            "chapters_completed": [],
            "started_at": None,
            "completed_at": None,
            "cancelled_at": None
        },
        {
            "campaign_id": "laboratorio-cristais",
            "title": "Capítulo 2 : Laboratório de Cristais Arcanos",
            "chapter": 2,
            "description": "Em um laboratório oculto nas profundezas da fortaleza inimiga, um cientista obcecado conduz experiências proibidas com fragmentos de energia arcana.",
            "full_description": "Em um laboratório oculto nas profundezas da fortaleza inimiga, um cientista obcecado conduz experiências proibidas com fragmentos de energia arcana. Sua última criação gerou uma reação instável, transformando o local em um campo de chamas e caos. O jogador deve atravessar o laboratório em colapso, evitando explosões e defendendo-se das máquinas de defesa ativadas pelo surto de energia.",
            "image": "./assets/images/campaign-thumb2.jpg",
            "thumbnail": "./assets/images/campaign-thumb2.jpg",
            "rewards": [
                {"type": "weapon", "name": "Bastão Arcano", "icon": "sword"},
                {"type": "armor", "name": "Manto de Cristal", "icon": "shield"},
                {"type": "health", "name": "Poção Vital", "icon": "heart"},
                {"type": "tech", "name": "Cristal Energético", "icon": "chip"}
            ],
            "is_locked": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": None,
            "active_character_id": None,
            "active_character_name": None,
            "current_chapter": None,
            "chapters_completed": [],
            "started_at": None,
            "completed_at": None,
            "cancelled_at": None
        },
        {
            "campaign_id": "coliseu-de-neon",
            "title": "Capítulo 3 : Coliseu de Neon",
            "chapter": 3,
            "description": "No coração da cidade subterrânea, em um beco cercado por prédios decadentes e iluminado apenas por letreiros de neon.",
            "full_description": "No coração da cidade subterrânea, em um beco cercado por prédios decadentes e iluminado apenas por letreiros de neon, ocorre o torneio clandestino mais brutal do submundo. Aqui, guerreiros e máquinas se enfrentam em lutas sangrentas, enquanto a multidão mascarada assiste em êxtase.",
            "image": "./assets/images/campaign-image3.jpg",
            "thumbnail": "./assets/images/campaign-image3.jpg",
            "rewards": [
                {"type": "weapon", "name": "Cetro do Caos", "icon": "sword"},
                {"type": "armor", "name": "Armadura Prismática", "icon": "shield"},
                {"type": "health", "name": "Elixir da Vida", "icon": "heart"},
                {"type": "tech", "name": "Núcleo de Energia", "icon": "chip"}
            ],
            "is_locked": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": None,
            "active_character_id": None,
            "active_character_name": None,
            "current_chapter": None,
            "chapters_completed": [],
            "started_at": None,
            "completed_at": None,
            "cancelled_at": None
        }
    ]
    
    result = campaigns_collection.insert_many(campaigns_data)

    created_campaigns = []
    for inserted_id in result.inserted_ids:
        campaign = campaigns_collection.find_one({"_id": inserted_id})
        serialized_campaign = serialize_campaign(campaign)
        if serialized_campaign:
            created_campaigns.append(serialized_campaign)
    
    return created_campaigns