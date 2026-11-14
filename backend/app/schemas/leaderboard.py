from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LeaderboardEntry(BaseModel):
    """
    Schema for a single leaderboard entry.
    
    Attributes:
        user_id: ID of the user
        username: Username for display
        completion_time_seconds: Time taken to complete the challenge
        timestamp: When the challenge was completed
        rank: Position in the leaderboard (optional, calculated on response)
    """
    user_id: int
    username: str
    completion_time_seconds: int
    timestamp: datetime
    rank: Optional[int] = None

    model_config = {
        "from_attributes": True
    }
