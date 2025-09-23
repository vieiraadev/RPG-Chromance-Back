from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CampaignProgress(BaseModel):
    """Model para armazenar o progresso de cada usuário em uma campanha"""
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    campaign_id: str  
    
    status: str = "in_progress"  
    active_character_id: Optional[str] = None
    active_character_name: Optional[str] = None
    current_chapter: int = 1
    chapters_completed: List[int] = Field(default_factory=list)
    score: int = 0
    battles_won: int = 0
    battles_lost: int = 0
    items_collected: List[str] = Field(default_factory=list)
    
    started_at: datetime = Field(default_factory=datetime.now)
    last_played_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }