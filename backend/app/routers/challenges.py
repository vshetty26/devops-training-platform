from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ChallengeResponse
from app.models import Challenge
from typing import List

router = APIRouter()

@router.get("/", response_model=List[ChallengeResponse])
async def list_challenges(
    db: Session = Depends(get_db),
    # TODO: Add authentication dependency
):
    """
    List all available challenges.
    
    Requirements: 2.1
    """
    challenges = db.query(Challenge).all()
    # TODO: Add completion status for authenticated user
    return [ChallengeResponse.model_validate(c) for c in challenges]

@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: str,
    db: Session = Depends(get_db),
    # TODO: Add authentication dependency
):
    """
    Get details for a specific challenge.
    
    Requirements: 2.1, 2.3
    """
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # TODO: Add completion status for authenticated user
    return ChallengeResponse.model_validate(challenge)
