from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta, datetime
from app.database import get_db
from app.schemas.user import LoginRequest, LoginResponse, UserResponse, UserCreate
from app.models.user import User
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.dependencies import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Creates a new user with hashed password storage.
    
    Args:
        user_data: Username and password for new account
        db: Database session
        
    Returns:
        Created user information (without password)
        
    Raises:
        HTTPException: 400 if username already exists
        
    Requirements: 1.5 (secure password storage)
    """
    logger.info(f"Registration attempt for username: {user_data.username}")
    
    try:
        new_user = create_user(db, user_data.username, user_data.password)
        logger.info(
            f"User registered successfully - username: {new_user.username}, "
            f"user_id: {new_user.id}, timestamp: {datetime.utcnow().isoformat()}"
        )
        return UserResponse.model_validate(new_user)
    except ValueError as e:
        logger.warning(f"Registration failed for username {user_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError:
        db.rollback()
        logger.warning(
            f"Registration failed - username already exists: {user_data.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    Validates credentials and creates an authenticated session via JWT.
    
    Args:
        login_data: Username and password credentials
        db: Database session
        
    Returns:
        JWT access token and user information
        
    Raises:
        HTTPException: 401 if credentials are invalid
        
    Requirements: 1.1 (authenticated session creation), 1.2 (invalid credentials error), 11.5 (logging)
    """
    logger.info(f"Login attempt for username: {login_data.username}")
    
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        # Log failed login attempt (WARNING level - security event)
        logger.warning(
            f"Failed login attempt - username: {login_data.username}, "
            f"reason: Invalid credentials, timestamp: {datetime.utcnow().isoformat()}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Log successful login (INFO level - normal operation)
    # Note: Do NOT log tokens or passwords
    logger.info(
        f"Successful login - username: {user.username}, user_id: {user.id}, "
        f"timestamp: {datetime.utcnow().isoformat()}"
    )
    
    return LoginResponse(
        token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Validates JWT token and returns user profile.
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        User profile information
        
    Requirements: 1.1 (authenticated session), 1.3 (user association)
    """
    return UserResponse.model_validate(current_user)
