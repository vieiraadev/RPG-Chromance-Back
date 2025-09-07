from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from pymongo.database import Database
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database

router = APIRouter(prefix="/api/campaigns", tags=["Campanhas"])


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
    """Retorna todas as campanhas disponíveis"""
    campaigns_collection = db["campaigns"]
    
    campaigns = []
    for doc in campaigns_collection.find().sort("chapter", 1):
        serialized_campaign = serialize_campaign(doc)
        if serialized_campaign:
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


@router.post("/seed")
async def seed_campaigns(db: Database = Depends(get_database)):
    """
    Popula o banco de dados com as campanhas dos capítulos 1, 2 e 3.
    ATENÇÃO: Remove todas as campanhas existentes antes de criar as novas!
    """
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
            "updated_at": datetime.now()
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
            "updated_at": datetime.now()
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
            "updated_at": datetime.now()
        }
    ]
    
    result = campaigns_collection.insert_many(campaigns_data)

    created_campaigns = []
    for inserted_id in result.inserted_ids:
        campaign = campaigns_collection.find_one({"_id": inserted_id})
        serialized_campaign = serialize_campaign(campaign)
        if serialized_campaign:
            created_campaigns.append(serialized_campaign)
    
    print(f"{len(created_campaigns)} campanhas criadas com sucesso!")
    
    return created_campaigns