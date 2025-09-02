from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.models.character import CharacterModel


class CharacterRepository:
    """Repositório para operações de personagens no MongoDB"""
    
    def __init__(self, db: Database):
        self.collection = db.characters
        self._create_indexes()
    
    def _create_indexes(self):
        """Cria índices para otimizar queries"""
        try:
            self.collection.create_index("user_id")
            self.collection.create_index("active")
            self.collection.create_index([("user_id", 1), ("active", -1)])
        except Exception as e:
            print(f"Erro ao criar índices: {e}")
    
    async def create(self, character_data: dict, user_id: str = None) -> CharacterModel:
        """Cria um novo personagem no banco"""
        try:
            character_data["user_id"] = user_id
            character_data["created_at"] = datetime.utcnow()
            character_data["active"] = True
            
            if hasattr(character_data.get("atributos"), "dict"):
                character_data["atributos"] = character_data["atributos"].dict()
            
            result = self.collection.insert_one(character_data)
            
            created_character = self.collection.find_one({"_id": result.inserted_id})
            
            return CharacterModel.from_mongo(created_character)
            
        except DuplicateKeyError:
            raise ValueError("Personagem já existe")
        except Exception as e:
            raise Exception(f"Erro ao criar personagem: {str(e)}")
    
    async def get_by_id(self, character_id: str, user_id: str = None) -> Optional[CharacterModel]:
        """Busca um personagem por ID"""
        try:
            query = {"_id": ObjectId(character_id), "active": True}
            if user_id:
                query["user_id"] = user_id
            
            character = self.collection.find_one(query)
            
            if character:
                return CharacterModel.from_mongo(character)
            return None
            
        except Exception as e:
            print(f"Erro ao buscar personagem: {e}")
            return None
    
    async def get_all(self, user_id: str = None, skip: int = 0, limit: int = 10) -> List[CharacterModel]:
        """Lista todos os personagens (com paginação)"""
        try:
            query = {"active": True}
            if user_id:
                query["user_id"] = user_id
            
            cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
            
            characters = []
            for doc in cursor:
                characters.append(CharacterModel.from_mongo(doc))
            
            return characters
            
        except Exception as e:
            print(f"Erro ao listar personagens: {e}")
            return []
    
    async def update(self, character_id: str, update_data: dict, user_id: str = None) -> Optional[CharacterModel]:
        """Atualiza um personagem"""
        try:
            query = {"_id": ObjectId(character_id), "active": True}
            if user_id:
                query["user_id"] = user_id
            
            update_data["updated_at"] = datetime.utcnow()
            
            if "atributos" in update_data and hasattr(update_data["atributos"], "dict"):
                update_data["atributos"] = update_data["atributos"].dict()
            
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            result = self.collection.find_one_and_update(
                query,
                {"$set": update_data},
                return_document=True
            )
            
            if result:
                return CharacterModel.from_mongo(result)
            return None
            
        except Exception as e:
            print(f"Erro ao atualizar personagem: {e}")
            return None
    
    async def delete(self, character_id: str, user_id: str = None) -> bool:
        """Soft delete de um personagem"""
        try:
            query = {"_id": ObjectId(character_id)}
            if user_id:
                query["user_id"] = user_id
            
            result = self.collection.update_one(
                query,
                {"$set": {"active": False, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Erro ao deletar personagem: {e}")
            return False
    
    async def count(self, user_id: str = None) -> int:
        """Conta o total de personagens ativos"""
        try:
            query = {"active": True}
            if user_id:
                query["user_id"] = user_id
            
            return self.collection.count_documents(query)
            
        except Exception:
            return 0