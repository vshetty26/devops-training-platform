from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ChallengeResponse
from app.models import Challenge, Attempt
from app.dependencies import get_current_user_optional
from app.models.user import User
from typing import List, Optional

router = APIRouter()

@router.get("/", response_model=List[ChallengeResponse])
async def list_challenges(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    List all available challenges with difficulty indicators and completion status.
    
    For authenticated users, includes completion status and best completion time for each challenge.
    
    Requirements: 
    - 2.1: Platform SHALL display all available challenges
    - 2.2: Platform SHALL display difficulty level tags
    - 2.5: Platform SHALL indicate challenge completion status for authenticated user
    - 1.3: Platform SHALL associate all challenge attempts with the authenticated user identifier
    """
    challenges = db.query(Challenge).all()
    
    result = []
    for challenge in challenges:
        challenge_data = ChallengeResponse.model_validate(challenge)
        
        # Check completion status and get best time for authenticated users
        if current_user:
            best_attempt = db.query(Attempt).filter(
                Attempt.user_id == current_user.id,
                Attempt.challenge_id == challenge.id,
                Attempt.success == True
            ).order_by(Attempt.completion_time_seconds.asc()).first()
            
            if best_attempt:
                challenge_data.completed = True
                challenge_data.completion_time_seconds = best_attempt.completion_time_seconds
        
        result.append(challenge_data)
    
    return result

@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get details for a specific challenge including brief, completion status, and best time.
    
    Returns challenge metadata with completion status and best completion time for authenticated users.
    
    Requirements: 
    - 2.3: Platform SHALL display a short incident description
    - 2.4: Platform SHALL navigate to challenge detail page
    - 2.5: Platform SHALL indicate challenge completion status
    - 1.3: Platform SHALL associate all challenge attempts with the authenticated user identifier
    """
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge_data = ChallengeResponse.model_validate(challenge)
    
    # Check completion status and get best time for authenticated users
    if current_user:
        best_attempt = db.query(Attempt).filter(
            Attempt.user_id == current_user.id,
            Attempt.challenge_id == challenge.id,
            Attempt.success == True
        ).order_by(Attempt.completion_time_seconds.asc()).first()
        
        if best_attempt:
            challenge_data.completed = True
            challenge_data.completion_time_seconds = best_attempt.completion_time_seconds
    
    return challenge_data

