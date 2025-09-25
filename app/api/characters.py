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
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/characters", tags=["Characters"])


def get_character_service(db: Database = Depends(get_database)) -> CharacterService:
    """Dependency injection para o serviço de personagens"""
    repository = CharacterRepository(db)
    return CharacterService(repository)


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_data: CharacterCreate,
    service: CharacterService = Depends(get_character_service),
    current_user_id: str = Depends(get_current_user)
):
    """Cria um novo personagem para o usuário autenticado"""
    try:
        character = await service.create_character(character_data, current_user_id)
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
    current_user_id: str = Depends(get_current_user) 
):
    """Lista apenas os personagens do usuário autenticado"""
    try:
        result = await service.list_characters(current_user_id, page, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/selected", response_model=CharacterResponse)
async def get_selected_character(
    service: CharacterService = Depends(get_character_service),
    current_user_id: str = Depends(get_current_user)
):
    """Busca o personagem atualmente selecionado do usuário"""
    try:
        character = await service.get_selected_character(current_user_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Nenhum personagem selecionado"
            )
        return character
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{character_id}/select", response_model=CharacterResponse)
async def select_character(
    character_id: str,
    service: CharacterService = Depends(get_character_service),
    current_user_id: str = Depends(get_current_user)
):
    """Seleciona um personagem específico"""
    try:
        character = await service.select_character(character_id, current_user_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Personagem não encontrado ou não autorizado"
            )
        return character
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    service: CharacterService = Depends(get_character_service),
    current_user_id: str = Depends(get_current_user) 
):
    """Busca um personagem específico"""
    try:
        character = await service.get_character(character_id, current_user_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Personagem não encontrado ou não autorizado"
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
    current_user_id: str = Depends(get_current_user)
):
    """Atualiza um personagem"""
    try:
        character = await service.update_character(character_id, update_data, current_user_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Personagem não encontrado ou não autorizado"
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
    current_user_id: str = Depends(get_current_user)
):
    """Remove um personagem"""
    try:
        success = await service.delete_character(character_id, current_user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Personagem não encontrado ou não autorizado"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

@router.get("/{character_id}/inventory", response_model=list, summary="Buscar inventário")
async def get_character_inventory(
    character_id: str,
    service: CharacterService = Depends(get_character_service),
    current_user_id: str = Depends(get_current_user)
):
    """Retorna o inventário completo do personagem"""
    try:
        from app.core.database import get_database
        db = next(get_database())
        from app.repositories.character_repo import CharacterRepository
        
        repo = CharacterRepository(db)
        inventory = await repo.get_inventory(character_id, current_user_id)
        
        return inventory
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )