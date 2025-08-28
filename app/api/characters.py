from typing import List

from fastapi import APIRouter

from app.schemas.character import PersonagemCreate, PersonagemOut

router = APIRouter(prefix="/api/personagem", tags=["Personagem"])


@router.post("", response_model=PersonagemOut, status_code=201, summary="Criar personagem")
async def criar_personagem(body: PersonagemCreate):
    return PersonagemOut(id="char-1", **body.model_dump())


@router.get("", response_model=List[PersonagemOut], summary="Listar personagens")
async def listar_personagens():
    return []


@router.get("/{id}", response_model=PersonagemOut, summary="Detalhar personagem")
async def detalhar_personagem(id: str):
    return PersonagemOut(
        id=id,
        nome="Nyx",
        raca="Humano",
        classe="Ladino",
        descricao="Netrunner em Neon City.",
        atributos={"forca": 6, "destreza": 12, "inteligencia": 16, "carisma": 11},
        faccao="Neon Syndicate",
        cyberwares=[{"nome": "Implante Óptico", "efeito": "Visão térmica"}],
    )
