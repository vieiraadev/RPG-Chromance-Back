from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator

class Atributos(BaseModel):
    """Schema para os atributos do personagem"""
    vida: int = Field(ge=8, le=20, default=10)
    energia: int = Field(ge=8, le=20, default=10)
    forca: int = Field(ge=8, le=20, default=10)
    inteligencia: int = Field(ge=8, le=20, default=10)
    
    @validator('*')
    def validate_attribute_range(cls, v):
        if not 8 <= v <= 20:
            raise ValueError('Atributo deve estar entre 8 e 20')
        return v

class CharacterCreate(BaseModel):
    """Schema para criar um personagem - corresponde ao frontend"""
    name: str = Field(..., min_length=1, max_length=100)
    raca: str = Field(..., min_length=1)
    classe: str = Field(..., min_length=1)
    descricao: Optional[str] = ""
    atributos: Atributos
    imageUrl: str = "assets/images/card-image1.jpg"
    
    @validator('name', 'raca', 'classe')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Campo não pode estar vazio')
        return v.strip()
    
    @validator('atributos')
    def validate_total_points(cls, v):
        total = v.vida + v.energia + v.forca + v.inteligencia
        if total > 52:
            raise ValueError(f'Total de pontos ({total}) excede o máximo permitido (52)')
        return v

class CharacterUpdate(BaseModel):
    """Schema para atualizar um personagem"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    raca: Optional[str] = None
    classe: Optional[str] = None
    descricao: Optional[str] = None
    atributos: Optional[Atributos] = None
    imageUrl: Optional[str] = None

class CharacterResponse(BaseModel):
    """Schema de resposta do personagem"""
    id: str = Field(..., alias="_id")
    name: str
    raca: str
    classe: str
    descricao: Optional[str] = ""
    atributos: Dict[str, int]
    imageUrl: str
    user_id: Optional[str] = None
    created_at: datetime
    active: bool = True
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CharacterListResponse(BaseModel):
    """Schema para listagem de personagens"""
    characters: list[CharacterResponse]
    total: int
    page: int = 1
    limit: int = 10
    pages: int = 1