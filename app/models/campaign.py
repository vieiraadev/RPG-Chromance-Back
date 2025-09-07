from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class Reward(BaseModel):
    type: str
    name: str
    icon: str


class Campaign(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    campaign_id: str
    title: str
    chapter: int  
    description: str
    full_description: str
    image: str
    thumbnail: str
    rewards: List[Reward]
    is_locked: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "campaign_id": "arena-sombras",
                "title": "Capítulo 1 : O Cubo das Sombras",
                "chapter": 1,
                "description": "Nas profundezas de uma catedral em ruínas...",
                "full_description": "Nas profundezas de uma catedral em ruínas...",
                "image": "./assets/images/campaign-thumb1.jpg",
                "thumbnail": "./assets/images/campaign-thumb1.jpg",
                "rewards": [
                    {"type": "weapon", "name": "Lâmina Cybernética", "icon": "sword"}
                ],
                "is_locked": False
            }
        }