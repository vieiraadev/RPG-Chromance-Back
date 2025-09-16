from typing import List, Optional
from app.repositories.character_repo import CharacterRepository
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse
from app.models.character import CharacterModel

class CharacterService:
    """Serviço de lógica de negócio para personagens"""
    
    def __init__(self, repository: CharacterRepository):
        self.repository = repository

    async def create_character(self, character_data: CharacterCreate, user_id: str = None) -> CharacterResponse:
        """Cria um novo personagem"""
        try:
            character_dict = character_data.dict()
            created_character = await self.repository.create(character_dict, user_id)
            return self._to_response(created_character)
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Erro ao criar personagem: {str(e)}")

    async def get_character(self, character_id: str, user_id: str = None) -> Optional[CharacterResponse]:
        """Busca um personagem por ID"""
        character = await self.repository.get_by_id(character_id, user_id)
        if character:
            return self._to_response(character)
        return None

    async def list_characters(
        self,
        user_id: str = None,
        page: int = 1,
        limit: int = 10
    ) -> dict:
        """Lista personagens com paginação"""
        skip = (page - 1) * limit
        characters = await self.repository.get_all(user_id, skip, limit)
        total = await self.repository.count(user_id)
        character_responses = [self._to_response(char) for char in characters]
        
        return {
            "characters": character_responses,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

    async def update_character(
        self,
        character_id: str,
        update_data: CharacterUpdate,
        user_id: str = None
    ) -> Optional[CharacterResponse]:
        """Atualiza um personagem"""
        update_dict = update_data.dict(exclude_unset=True)
        if not update_dict:
            raise ValueError("Nenhum campo para atualizar")
            
        updated_character = await self.repository.update(character_id, update_dict, user_id)
        if updated_character:
            return self._to_response(updated_character)
        return None

    async def delete_character(self, character_id: str, user_id: str = None) -> bool:
        """Remove um personagem (soft delete)"""
        return await self.repository.delete(character_id, user_id)

    async def select_character(self, character_id: str, user_id: str = None) -> Optional[CharacterResponse]:
        """Seleciona um personagem (desmarca outros e marca este)"""
        try:
            await self.repository.unselect_all_characters(user_id)
            
            updated_character = await self.repository.update(
                character_id, 
                {"is_selected": True}, 
                user_id
            )
            
            if updated_character:
                return self._to_response(updated_character)
            return None
        except Exception as e:
            raise Exception(f"Erro ao selecionar personagem: {str(e)}")

    async def get_selected_character(self, user_id: str = None) -> Optional[CharacterResponse]:
        """Busca o personagem atualmente selecionado do usuário"""
        character = await self.repository.get_selected_character(user_id)
        if character:
            return self._to_response(character)
        return None

    def _to_response(self, character: CharacterModel) -> CharacterResponse:
        """Converte modelo para response"""
        data = character.dict()
        if "id" in data and data["id"]:
            data["_id"] = data["id"]
        elif "_id" not in data:
            data["_id"] = str(data.get("id", ""))
        return CharacterResponse(**data)