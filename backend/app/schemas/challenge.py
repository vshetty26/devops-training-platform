from pydantic import BaseModel
from typing import Optional

class ChallengeResponse(BaseModel):
    """Schema for challenge data in responses"""
    id: str
    title: str
    difficulty: str
    brief: str
    completed: Optional[bool] = False

    class Config:
        from_attributes = True
