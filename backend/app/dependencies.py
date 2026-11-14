"""
FastAPI dependencies for authentication and request validation.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import decode_access_token, get_user_by_id
from app.models.user import User

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Validates the JWT token from the Authorization header and returns
    the corresponding user object.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
        
    Requirements: 1.1, 1.4 (authentication and access control)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Decode and validate token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract user ID from token payload
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Retrieve user from database
    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency.
    
    Returns the current user if authenticated, None otherwise.
    Does not raise an exception if no credentials are provided.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        
        user_id = int(user_id_str)
        user = get_user_by_id(db, user_id)
        return user
    except (ValueError, Exception):
        return None
