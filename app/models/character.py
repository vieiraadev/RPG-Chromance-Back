from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from bson import ObjectId

class InventoryItem(BaseModel):
    """Item do inventário"""
    id: str
    name: str
    description: str
    type: str 
    chapter: int
    campaign_id: str
    obtained_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = {}

class CharacterModel(BaseModel):
    """Modelo de dados do personagem no MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    name: str
    raca: str
    classe: str
    descricao: Optional[str] = ""
    atributos: Dict[str, int]
    inventory: List[InventoryItem] = [] 
    imageUrl: str = "assets/images/default-avatar.png"
    user_id: Optional[str] = None
    is_selected: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

    def to_mongo(self):
        """Converte para formato MongoDB"""
        data = self.dict(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"]:
            data["_id"] = ObjectId(data["_id"])
        elif "_id" in data:
            data.pop("_id")
        
        if "inventory" in data:
            data["inventory"] = [
                item.dict() if hasattr(item, 'dict') else item 
                for item in data["inventory"]
            ]
        
        return data

    @classmethod
    def from_mongo(cls, data: dict):
        """Cria instância a partir de documento MongoDB"""
        if data and "_id" in data:
            data["_id"] = str(data["_id"])
        
        if "inventory" in data and data["inventory"]:
            data["inventory"] = [
                InventoryItem(**item) if isinstance(item, dict) else item 
                for item in data["inventory"]
            ]
        
        return cls(**data)