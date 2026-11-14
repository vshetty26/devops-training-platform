"""
User-related Pydantic schemas with enhanced validation.

Requirements: 13.5, 14.1, 14.2, 14.3
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class UserCreate(BaseModel):
    """
    Schema for user creation with input validation.
    
    Requirements: 14.1, 14.2, 14.3
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Validate username format.
        
        Requirements: 14.2 (input validation)
        """
        # Allow alphanumeric, underscore, and hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'Username must contain only letters, numbers, underscores, and hyphens'
            )
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength.
        
        Requirements: 14.2 (input validation), 1.5 (secure credentials)
        """
        # Check for at least one letter and one number
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """
    Schema for login request with input validation.
    
    Requirements: 14.1, 14.2
    """
    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Username"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Password"
    )


class LoginResponse(BaseModel):
    """Schema for login response"""
    token: str
    user: UserResponse

