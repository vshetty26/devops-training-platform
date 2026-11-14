"""
Validation-related Pydantic schemas.

Requirements: 13.5
"""
from pydantic import BaseModel, Field
from typing import Optional


class ValidationResponse(BaseModel):
    """
    Schema for validation result responses.
    
    Requirements: 6.2, 6.3, 6.4
    """
    success: bool = Field(..., description="Whether validation passed")
    message: str = Field(..., description="Validation result message")
    hint: Optional[str] = Field(None, description="Hint for failed validations")

