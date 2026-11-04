from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base

class Attempt(Base):
    """
    Attempt model recording validation attempts for challenges.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        challenge_id: Foreign key to challenges table
        session_id: Foreign key to sessions table
        success: Whether the validation passed
        completion_time_seconds: Time from session start to successful validation
        created_at: Timestamp of the validation attempt
    """
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(String, ForeignKey("challenges.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    success = Column(Boolean, nullable=False)
    completion_time_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_attempts_user_challenge', 'user_id', 'challenge_id'),
        Index('idx_attempts_challenge_success', 'challenge_id', 'success', 'completion_time_seconds'),
    )
