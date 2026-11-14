"""
Session-related Pydantic schemas with enhanced validation.

Requirements: 13.5, 14.1, 14.2, 14.3
"""
from pydantic import BaseModel, Field, field_validator
import re


class SessionCreateRequest(BaseModel):
    """
    Schema for session creation request with input validation.
    
    Requirements: 14.1, 14.2
    """
    challenge_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Challenge identifier"
    )
    
    @field_validator('challenge_id')
    @classmethod
    def validate_challenge_id(cls, v: str) -> str:
        """
        Validate challenge ID format.
        
        Requirements: 14.2 (input validation)
        """
        # Allow alphanumeric and hyphens (typical challenge ID format)
        if not re.match(r'^[a-zA-Z0-9-]+$', v):
            raise ValueError(
                'Challenge ID must contain only letters, numbers, and hyphens'
            )
        return v


class SessionResponse(BaseModel):
    """Schema for session data in responses"""
    session_id: str
    container_id: str
    websocket_url: str
    timeout_seconds: int

