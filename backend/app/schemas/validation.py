from pydantic import BaseModel
from typing import Optional

class ValidationResponse(BaseModel):
    """Schema for validation result responses"""
    success: bool
    message: str
    hint: Optional[str] = None
