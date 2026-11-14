"""
Authentication service for user management and JWT operations.

Handles password hashing, token generation/validation, and user authentication.

Security Features:
- Bcrypt password hashing
- JWT token generation with configurable expiration
- Environment-based secret key configuration
- Secure token validation

Requirements: 1.1, 1.2, 1.5, 14.1, 14.2, 14.5
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings from configuration (Requirements: 14.4, 14.5)
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

# Warn if using default secret key in production
if settings.is_production() and "dev-secret-key" in SECRET_KEY:
    logger.critical(
        "SECURITY WARNING: Using default JWT secret key in production! "
        "Set JWT_SECRET_KEY environment variable immediately!"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
        
    Requirements: 1.5 (secure password storage)
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Requirements: 1.1 (authenticated session creation)
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password to verify
        
    Returns:
        User object if authentication succeeds, None otherwise
        
    Requirements: 1.1, 1.2 (credential validation)
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(db: Session, username: str, password: str) -> User:
    """
    Create a new user with hashed password.
    
    Args:
        db: Database session
        username: Unique username
        password: Plain text password (will be hashed)
        
    Returns:
        Created User object
        
    Raises:
        ValueError: If username already exists
        
    Requirements: 1.5 (secure password storage)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise ValueError("Username already exists")
    
    # Create new user with hashed password
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Retrieve a user by ID.
    
    Args:
        db: Database session
        user_id: User ID to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()
