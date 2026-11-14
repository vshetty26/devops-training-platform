from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.schemas.leaderboard import LeaderboardEntry
from app.models.attempt import Attempt
from app.models.user import User
from app.models.challenge import Challenge
from typing import List

router = APIRouter()


@router.get("/", response_model=List[LeaderboardEntry])
async def get_global_leaderboard(
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Get global leaderboard with top fastest completions across all challenges.
    
    Returns the top performers ranked by completion time (fastest first).
    Limited to top 10 results by default.
    
    Requirements:
    - 9.1: Platform SHALL display a leaderboard page with user rankings
    - 9.2: Platform SHALL rank users by challenge completion, then by completion time
    - 9.3: Platform SHALL display username and completion time for each entry
    - 9.4: Leaderboard SHALL update within 5 seconds after challenge completion
    
    Args:
        db: Database session
        limit: Maximum number of entries to return (default: 10)
        
    Returns:
        List of leaderboard entries sorted by completion time ascending
    """
    # Query successful attempts with user information
    # Join Attempt with User to get username
    # Filter for successful attempts only
    # Order by completion_time_seconds ascending (fastest first)
    # Limit to top N results
    
    query = (
        db.query(
            Attempt.user_id,
            User.username,
            Attempt.completion_time_seconds,
            Attempt.created_at.label('timestamp')
        )
        .join(User, Attempt.user_id == User.id)
        .filter(
            and_(
                Attempt.success == True,
                Attempt.completion_time_seconds.isnot(None)
            )
        )
        .order_by(Attempt.completion_time_seconds.asc())
        .limit(limit)
    )
    
    results = query.all()
    
    # Add rank to each entry
    leaderboard = []
    for idx, result in enumerate(results, start=1):
        entry = LeaderboardEntry(
            user_id=result.user_id,
            username=result.username,
            completion_time_seconds=result.completion_time_seconds,
            timestamp=result.timestamp,
            rank=idx
        )
        leaderboard.append(entry)
    
    return leaderboard


@router.get("/{challenge_id}", response_model=List[LeaderboardEntry])
async def get_challenge_leaderboard(
    challenge_id: str,
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Get leaderboard for a specific challenge.
    
    Returns top performers for a single challenge ranked by completion time.
    Limited to top 10 results by default.
    
    Requirements:
    - 9.1: Platform SHALL display a leaderboard page with user rankings
    - 9.2: Platform SHALL rank users by challenge completion, then by completion time
    - 9.3: Platform SHALL display username and completion time for each entry
    - 9.5: Platform SHALL provide separate leaderboard views per challenge
    
    Args:
        challenge_id: ID of the challenge to get rankings for
        db: Database session
        limit: Maximum number of entries to return (default: 10)
        
    Returns:
        List of leaderboard entries for the challenge sorted by completion time
        
    Raises:
        HTTPException: 404 if challenge not found
    """
    # Verify challenge exists
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Query successful attempts for this specific challenge
    # Join with User to get username
    # Filter for successful attempts and specific challenge
    # Order by completion_time_seconds ascending (fastest first)
    # Limit to top N results
    
    query = (
        db.query(
            Attempt.user_id,
            User.username,
            Attempt.completion_time_seconds,
            Attempt.created_at.label('timestamp')
        )
        .join(User, Attempt.user_id == User.id)
        .filter(
            and_(
                Attempt.challenge_id == challenge_id,
                Attempt.success == True,
                Attempt.completion_time_seconds.isnot(None)
            )
        )
        .order_by(Attempt.completion_time_seconds.asc())
        .limit(limit)
    )
    
    results = query.all()
    
    # Add rank to each entry
    leaderboard = []
    for idx, result in enumerate(results, start=1):
        entry = LeaderboardEntry(
            user_id=result.user_id,
            username=result.username,
            completion_time_seconds=result.completion_time_seconds,
            timestamp=result.timestamp,
            rank=idx
        )
        leaderboard.append(entry)
    
    return leaderboard
