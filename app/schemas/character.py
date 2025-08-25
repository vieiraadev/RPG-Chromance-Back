from pydantic import BaseModel, Field
from typing import List, Optional

class Atributos(BaseModel):
    forca: int = Field(ge=0, le=20, examples=[8])
    destreza: int = Field(ge=0, le=20, examples=[12])
    inteligencia: int = Field(ge=0, le=20, examples=[16])
    carisma: int = Field(ge=0, le=20, examples=[11])

class Cyberware(BaseModel):
    nome: str
    efeito: Optional[str] = ""

class PersonagemCreate(BaseModel):
    nome: str
    raca: str      
    classe: str    
    descricao: Optional[str] = ""
    atributos: Atributos
    faccao: Optional[str] = "Street Runners"
    cyberwares: List[Cyberware] = []

class PersonagemOut(PersonagemCreate):
    id: str
    nivel: int = 1
    vida: int = 100
    exp: int = 0
    inventario: List[str] = []
