from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Session(Base):
    """
    Session model representing a user's challenge attempt instance.
    
    Attributes:
        id: Unique session identifier (UUID)
        user_id: Foreign key to users table
        challenge_id: Foreign key to challenges table
        container_id: Docker container ID for this session
        status: Session status (active, completed, timeout, terminated)
        created_at: Session start timestamp
        timeout_at: When the session will automatically terminate
        terminated_at: When the session was actually terminated (NULL if still active)
    """
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(String, ForeignKey("challenges.id"), nullable=False)
    container_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    timeout_at = Column(DateTime(timezone=True), nullable=False)
    terminated_at = Column(DateTime(timezone=True), nullable=True)
