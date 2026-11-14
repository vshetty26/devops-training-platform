"""
Unit tests for authentication service.

Tests password hashing, JWT token operations, and user authentication.
"""
import pytest
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    authenticate_user,
    create_user,
    get_user_by_id
)


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestPasswordHashing:
    """Test password hashing and verification - Requirement 1.5"""
    
    def test_password_hash_is_different_from_plain(self):
        """Hashed password should not match plain text"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
    
    def test_verify_correct_password(self):
        """Correct password should verify successfully"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Incorrect password should fail verification"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False
    
    def test_same_password_different_hashes(self):
        """Same password should generate different hashes (salt verification)"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and validation - Requirement 1.1"""
    
    def test_create_token_with_default_expiry(self):
        """Token should be created with default expiration"""
        token = create_access_token({"sub": "123"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_with_custom_expiry(self):
        """Token should be created with custom expiration"""
        expires = timedelta(minutes=60)
        token = create_access_token({"sub": "123"}, expires_delta=expires)
        assert token is not None
    
    def test_decode_valid_token(self):
        """Valid token should decode successfully"""
        user_id = "123"
        token = create_access_token({"sub": user_id})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
    
    def test_decode_invalid_token(self):
        """Invalid token should return None"""
        invalid_token = "invalid.token.here"
        payload = decode_access_token(invalid_token)
        assert payload is None
    
    def test_decode_expired_token(self):
        """Expired token should return None"""
        # Create token that expires immediately
        token = create_access_token({"sub": "123"}, expires_delta=timedelta(seconds=-1))
        payload = decode_access_token(token)
        assert payload is None


class TestUserAuthentication:
    """Test user authentication logic - Requirements 1.1, 1.2"""
    
    def test_authenticate_valid_user(self, db_session):
        """Valid credentials should authenticate successfully"""
        # Create test user
        username = "testuser"
        password = "testpass123"
        user = create_user(db_session, username, password)
        
        # Authenticate
        authenticated_user = authenticate_user(db_session, username, password)
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.username == username
    
    def test_authenticate_invalid_username(self, db_session):
        """Non-existent username should fail authentication"""
        authenticated_user = authenticate_user(db_session, "nonexistent", "password")
        assert authenticated_user is None
    
    def test_authenticate_invalid_password(self, db_session):
        """Incorrect password should fail authentication"""
        # Create test user
        username = "testuser"
        password = "testpass123"
        create_user(db_session, username, password)
        
        # Try to authenticate with wrong password
        authenticated_user = authenticate_user(db_session, username, "wrongpass")
        assert authenticated_user is None


class TestUserCreation:
    """Test user creation and retrieval - Requirements 1.3, 1.5"""
    
    def test_create_user_success(self, db_session):
        """User should be created with hashed password"""
        username = "testuser"
        password = "testpass123"
        
        user = create_user(db_session, username, password)
        
        assert user is not None
        assert user.id is not None
        assert user.username == username
        assert user.password_hash != password
        assert user.created_at is not None
    
    def test_create_duplicate_user(self, db_session):
        """Creating duplicate username should raise ValueError"""
        username = "testuser"
        password = "testpass123"
        
        create_user(db_session, username, password)
        
        with pytest.raises(ValueError, match="Username already exists"):
            create_user(db_session, username, password)
    
    def test_get_user_by_id_exists(self, db_session):
        """Retrieving existing user by ID should succeed"""
        username = "testuser"
        password = "testpass123"
        created_user = create_user(db_session, username, password)
        
        retrieved_user = get_user_by_id(db_session, created_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == username
    
    def test_get_user_by_id_not_exists(self, db_session):
        """Retrieving non-existent user should return None"""
        retrieved_user = get_user_by_id(db_session, 99999)
        assert retrieved_user is None
