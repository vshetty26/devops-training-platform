from pydantic import BaseModel

class SessionCreateRequest(BaseModel):
    """Schema for session creation request"""
    challenge_id: str

class SessionResponse(BaseModel):
    """Schema for session data in responses"""
    session_id: str
    container_id: str
    websocket_url: str
    timeout_seconds: int
