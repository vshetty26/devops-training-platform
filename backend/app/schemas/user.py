from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """Schema for user creation"""
    username: str
    password: str

class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Schema for login response"""
    token: str
    user: UserResponse
