from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pymongo.database import Database

from app.core.database import get_database
from app.repositories.character_repo import CharacterRepository
from app.services.character_service import CharacterService
from app.schemas.character import (
    CharacterCreate, 
    CharacterUpdate, 
    CharacterResponse,
    CharacterListResponse
)

router = APIRouter(prefix="/api/characters", tags=["Characters"])


def get_character_service(db: Database = Depends(get_database)) -> CharacterService:
    """Dependency injection para o serviço de personagens"""
    repository = CharacterRepository(db)
    return CharacterService(repository)


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_data: CharacterCreate,
    service: CharacterService = Depends(get_character_service),
    user_id: Optional[str] = None 
):
    """
    Cria um novo personagem
    """
    try:
        user_id = user_id or "user123"
        
        character = await service.create_character(character_data, user_id)
        return character
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=dict)
async def list_characters(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(100, ge=1, le=1000, description="Itens por página"), 
    service: CharacterService = Depends(get_character_service),
    user_id: Optional[str] = None
):
    """
    Lista todos os personagens
    """
    try:
        user_id = user_id or "user123"
        
        result = await service.list_characters(user_id, page, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    service: CharacterService = Depends(get_character_service),
    user_id: Optional[str] = None
):
    """
    Busca um personagem específico por ID
    """
    try:
        user_id = user_id or "user123"
        
        character = await service.get_character(character_id, user_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Personagem não encontrado"
            )
        return character
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    update_data: CharacterUpdate,
    service: CharacterService = Depends(get_character_service),
    user_id: Optional[str] = None
):
    """
    Atualiza um personagem existente
    """
    try:
        user_id = user_id or "user123"
        
        character = await service.update_character(character_id, update_data, user_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Personagem não encontrado"
            )
        return character
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: str,
    service: CharacterService = Depends(get_character_service),
    user_id: Optional[str] = None
):
    """
    Remove um personagem (soft delete)
    """
    try:
        user_id = user_id or "user123"
        
        success = await service.delete_character(character_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Personagem não encontrado"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))