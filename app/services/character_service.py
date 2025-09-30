from typing import List, Optional
from app.repositories.character_repo import CharacterRepository
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse
from app.models.character import CharacterModel


class CharacterService:
    """Serviço para lógica de negócio de personagens"""
    
    def __init__(self, repository: CharacterRepository):
        self.repository = repository
    
    async def create_character(self, character_data: CharacterCreate, user_id: str = None) -> CharacterResponse:
        """Cria um novo personagem"""
        character_dict = character_data.dict()
        character = await self.repository.create(character_dict, user_id)
        return CharacterResponse(**character.dict(by_alias=True))
    
    async def list_characters(self, user_id: str = None, page: int = 1, limit: int = 10) -> dict:
        """Lista personagens com paginação"""
        skip = (page - 1) * limit
        
        characters = await self.repository.get_all(user_id, skip, limit)
        total = await self.repository.count(user_id)
        pages = (total + limit - 1) // limit
        
        characters_dict = []
        for char in characters:
            char_dict = char.dict(by_alias=True)
            
            if 'inventory' not in char_dict or char_dict['inventory'] is None:
                char_dict['inventory'] = []
            
            if char_dict['inventory']:
                char_dict['inventory'] = [
                    item.dict() if hasattr(item, 'dict') else item 
                    for item in char_dict['inventory']
                ]
            
            characters_dict.append(char_dict)
        
        return {
            "characters": characters_dict,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages
        }
    
    async def get_character(self, character_id: str, user_id: str = None) -> Optional[CharacterResponse]:
        """Busca um personagem por ID"""
        character = await self.repository.get_by_id(character_id, user_id)
        if character:
            char_dict = character.dict(by_alias=True)
            
            if 'inventory' not in char_dict or char_dict['inventory'] is None:
                char_dict['inventory'] = []
            
            return CharacterResponse(**char_dict)
        return None
    
    async def update_character(
        self, 
        character_id: str, 
        update_data: CharacterUpdate, 
        user_id: str = None
    ) -> Optional[CharacterResponse]:
        """Atualiza um personagem"""
        update_dict = update_data.dict(exclude_unset=True)
        character = await self.repository.update(character_id, update_dict, user_id)
        if character:
            char_dict = character.dict(by_alias=True)
            
            if 'inventory' not in char_dict or char_dict['inventory'] is None:
                char_dict['inventory'] = []
                
            return CharacterResponse(**char_dict)
        return None
    
    async def delete_character(self, character_id: str, user_id: str = None) -> bool:
        """Remove um personagem (soft delete)"""
        return await self.repository.delete(character_id, user_id)
    
    async def select_character(self, character_id: str, user_id: str = None) -> Optional[CharacterResponse]:
        """Seleciona um personagem"""
        await self.repository.unselect_all_characters(user_id)
        
        character = await self.repository.select_character_by_id(character_id, user_id)
        if character:
            char_dict = character.dict(by_alias=True)
            
            if 'inventory' not in char_dict or char_dict['inventory'] is None:
                char_dict['inventory'] = []
                
            return CharacterResponse(**char_dict)
        return None
    
    async def get_selected_character(self, user_id: str = None) -> Optional[CharacterResponse]:
        """Busca o personagem selecionado"""
        character = await self.repository.get_selected_character(user_id)
        if character:
            char_dict = character.dict(by_alias=True)
            
            if 'inventory' not in char_dict or char_dict['inventory'] is None:
                char_dict['inventory'] = []
                
            return CharacterResponse(**char_dict)
        return None
    
    async def use_item(
        self, 
        character_id: str, 
        item_id: str, 
        user_id: str = None
    ) -> Optional[CharacterResponse]:
        """Usa um item do inventário, aplicando bônus aos atributos"""
        character = await self.repository.get_by_id(character_id, user_id)
        if not character:
            return None
        
        item = None
        item_index = None
        for idx, inv_item in enumerate(character.inventory):
            if inv_item.id == item_id:
                item = inv_item
                item_index = idx
                break
        
        if not item:
            raise ValueError("Item não encontrado no inventário")
        
        bonus = self._extract_item_bonus(item)
        
        new_attributes = character.atributos.copy()
        for attr, value in bonus.items():
            if attr in new_attributes:
                new_attributes[attr] = min(20, new_attributes[attr] + value)
        
        new_inventory = [inv_item for idx, inv_item in enumerate(character.inventory) if idx != item_index]
        
        update_dict = {
            "atributos": new_attributes,
            "inventory": [item.dict() if hasattr(item, 'dict') else item for item in new_inventory]
        }
        
        character = await self.repository.update(character_id, update_dict, user_id)
        if character:
            char_dict = character.dict(by_alias=True)
            if 'inventory' not in char_dict or char_dict['inventory'] is None:
                char_dict['inventory'] = []
            return CharacterResponse(**char_dict)
        return None

    def _extract_item_bonus(self, item) -> dict:
        """Extrai os bônus de atributos de um item"""
        bonus = {}

        if hasattr(item, 'metadata') and item.metadata:
            if 'attribute_bonus' in item.metadata:
                return item.metadata['attribute_bonus']
            if 'power' in item.metadata:
                power = item.metadata['power']
                if isinstance(power, str):
                    bonus.update(self._parse_attribute_string(power))
            
            if 'effect' in item.metadata:
                effect = item.metadata['effect']
                if isinstance(effect, str):
                    bonus.update(self._parse_attribute_string(effect))
        
        return bonus

    def _parse_attribute_string(self, text: str) -> dict:
        """Parseia strings como '+3 Força' para extrair bônus"""
        bonus = {}
        text = text.lower()
        
        attr_map = {
            'vida': 'vida',
            'energy': 'energia',
            'energia': 'energia',
            'força': 'forca',
            'forca': 'forca',
            'strength': 'forca',
            'inteligência': 'inteligencia',
            'inteligencia': 'inteligencia',
            'intelligence': 'inteligencia'
        }
        
        import re
        pattern = r'[+]?(\d+)\s*(?:de\s+)?(\w+)'
        matches = re.findall(pattern, text)
        
        for value, attr_name in matches:
            attr_key = attr_map.get(attr_name.lower())
            if attr_key:
                bonus[attr_key] = int(value)
        
        return bonus