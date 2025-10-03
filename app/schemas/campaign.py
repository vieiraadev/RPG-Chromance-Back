from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class RewardSchema(BaseModel):
    type: str
    name: str
    icon: str

class CampaignCreate(BaseModel):
    """Schema para criar uma campanha"""
    campaign_id: str
    title: str
    chapter: int
    description: str
    full_description: str
    image: str
    thumbnail: str
    rewards: List[RewardSchema]
    is_locked: bool = False

class CampaignUpdate(BaseModel):
    """Schema para atualizar uma campanha"""
    title: Optional[str] = None
    description: Optional[str] = None
    full_description: Optional[str] = None
    image: Optional[str] = None
    thumbnail: Optional[str] = None
    rewards: Optional[List[RewardSchema]] = None
    is_locked: Optional[bool] = None
    status: Optional[str] = None
    active_character_id: Optional[str] = None
    active_character_name: Optional[str] = None
    current_chapter: Optional[int] = None
    chapters_completed: Optional[List[int]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

class CampaignOut(BaseModel):
    """Schema de resposta de campanha"""
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    id: str
    campaign_id: str
    title: str
    chapter: int
    description: str
    full_description: str
    image: str
    thumbnail: str
    rewards: List[RewardSchema]
    is_locked: bool
    user_id: Optional[str] = None
    status: Optional[str] = None
    active_character_id: Optional[str] = None
    active_character_name: Optional[str] = None
    current_chapter: Optional[int] = None
    chapters_completed: List[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    last_played_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

class StartCampaignRequest(BaseModel):
    """Schema para iniciar uma campanha"""
    character_id: str
    character_name: str
    campaign_id: str

class CompleteCampaignChapterRequest(BaseModel):
    """Schema para completar um capítulo"""
    character_id: str
    chapter_completed: int