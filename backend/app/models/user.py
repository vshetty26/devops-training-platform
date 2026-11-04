from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """
    User model for authentication and tracking.
    
    Attributes:
        id: Primary key
        username: Unique username for login
        password_hash: Hashed password (never store plain text)
        created_at: Timestamp of user registration
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
