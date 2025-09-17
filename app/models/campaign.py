from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class Reward(BaseModel):
    type: str
    name: str
    icon: str

class Campaign(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    id: Optional[str] = None 
    campaign_id: str
    title: str
    chapter: int
    description: str
    full_description: str
    image: str
    thumbnail: str
    rewards: List[Reward]
    is_locked: bool = False
    
    user_id: Optional[str] = None 
    status: Optional[str] = None 
    active_character_id: Optional[str] = None
    active_character_name: Optional[str] = None
    current_chapter: Optional[int] = None
    chapters_completed: List[int] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None