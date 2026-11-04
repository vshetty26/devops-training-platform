from sqlalchemy import Column, String, Text
from app.database import Base

class Challenge(Base):
    """
    Challenge model representing a DevOps troubleshooting scenario.
    
    Attributes:
        id: Unique challenge identifier (e.g., 'nginx-502')
        title: Display title for the challenge
        difficulty: Difficulty level (easy, medium, hard)
        brief: Problem description presented to users
        metadata: JSON string containing hints and other challenge data
    """
    __tablename__ = "challenges"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    brief = Column(Text, nullable=False)
    metadata = Column(Text)  # Stores JSON
