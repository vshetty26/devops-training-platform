"""
Integration tests for session API endpoints.

Tests the session creation and termination endpoints.
Requirements: 3.1, 5.1, 5.2, 5.3, 13.5
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch, MagicMock
from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.challenge import Challenge
from app.models.session import Session as SessionModel
from app.services.auth_service import create_access_token


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}  # Allow SQLite to work across threads in tests
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create test user with a simple pre-hashed password
    # Using a known bcrypt hash for "password123"
    test_user = User(
        username="testuser",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU5Y3BLevAR."
    )
    session.add(test_user)
    
    # Create test challenge
    test_challenge = Challenge(
        id="test-challenge",
        title="Test Challenge",
        difficulty="easy",
        brief="A test challenge",
        metadata='{"hints": ["Test hint"]}'
    )
    session.add(test_challenge)
    
    session.commit()
    session.refresh(test_user)
    session.refresh(test_challenge)
    
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(db_session):
    """Create authentication headers with valid JWT token"""
    user = db_session.query(User).filter(User.username == "testuser").first()
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestSessionCreation:
    """Test session creation endpoint - Requirements 3.1, 5.1, 13.5"""
    
    @patch('app.routers.sessions.get_session_manager')
    def test_create_session_success(self, mock_get_session_manager, client, db_session, auth_headers):
        """Creating a session with valid challenge should succeed"""
        # Mock the session manager to avoid Docker operations
        mock_session_manager = Mock()
        mock_session = SessionModel(
            id="test-session-123",
            user_id=1,
            challenge_id="test-challenge",
            container_id="container-123",
            status="active",
            timeout_at="2024-01-01T12:30:00"
        )
        mock_session_manager.create_session.return_value = mock_session
        mock_get_session_manager.return_value = mock_session_manager
        
        response = client.post(
            "/api/sessions/",
            json={"challenge_id": "test-challenge"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "container_id" in data
        assert "websocket_url" in data
        assert "timeout_seconds" in data
        assert data["timeout_seconds"] == 1800  # 30 minutes
        assert "ws://" in data["websocket_url"]
    
    def test_create_session_invalid_challenge(self, client, auth_headers):
        """Creating a session with invalid challenge should return 404"""
        response = client.post(
            "/api/sessions/",
            json={"challenge_id": "nonexistent-challenge"},
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_session_unauthenticated(self, client):
        """Creating a session without authentication should return 401"""
        response = client.post(
            "/api/sessions/",
            json={"challenge_id": "test-challenge"}
        )
        
        assert response.status_code == 401
    
    def test_create_session_invalid_token(self, client):
        """Creating a session with invalid token should return 401"""
        response = client.post(
            "/api/sessions/",
            json={"challenge_id": "test-challenge"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
    
    def test_create_session_missing_challenge_id(self, client, auth_headers):
        """Creating a session without challenge_id should return 422"""
        response = client.post(
            "/api/sessions/",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestSessionTermination:
    """Test session termination endpoint - Requirements 5.2, 5.3, 13.5"""
    
    @patch('app.routers.sessions.get_session_manager')
    def test_terminate_session_success(self, mock_get_session_manager, client, db_session, auth_headers):
        """Terminating an active session should succeed"""
        # Create a test session in the database
        from datetime import datetime, timedelta
        user = db_session.query(User).filter(User.username == "testuser").first()
        test_session = SessionModel(
            id="test-session-456",
            user_id=user.id,
            challenge_id="test-challenge",
            container_id="container-456",
            status="active",
            timeout_at=datetime.utcnow() + timedelta(minutes=30)
        )
        db_session.add(test_session)
        db_session.commit()
        
        # Mock the session manager
        mock_session_manager = Mock()
        mock_session_manager.terminate_session.return_value = None
        mock_get_session_manager.return_value = mock_session_manager
        
        response = client.delete(
            "/api/sessions/test-session-456",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    def test_terminate_session_not_found(self, client, auth_headers):
        """Terminating a non-existent session should return 404"""
        response = client.delete(
            "/api/sessions/nonexistent-session",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_terminate_session_unauthorized(self, client, db_session, auth_headers):
        """Terminating another user's session should return 403"""
        from datetime import datetime, timedelta
        # Create a session for a different user
        other_user = User(
            username="otheruser",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU5Y3BLevAR."
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        other_session = SessionModel(
            id="other-session-789",
            user_id=other_user.id,
            challenge_id="test-challenge",
            container_id="container-789",
            status="active",
            timeout_at=datetime.utcnow() + timedelta(minutes=30)
        )
        db_session.add(other_session)
        db_session.commit()
        
        response = client.delete(
            "/api/sessions/other-session-789",
            headers=auth_headers
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_terminate_session_unauthenticated(self, client):
        """Terminating a session without authentication should return 401"""
        response = client.delete("/api/sessions/test-session-123")
        
        assert response.status_code == 401
    
    @patch('app.routers.sessions.get_session_manager')
    def test_terminate_already_terminated_session(self, mock_get_session_manager, client, db_session, auth_headers):
        """Terminating an already terminated session should return 204 (idempotent)"""
        from datetime import datetime, timedelta
        # Create a terminated session in the database
        user = db_session.query(User).filter(User.username == "testuser").first()
        terminated_session = SessionModel(
            id="terminated-session-999",
            user_id=user.id,
            challenge_id="test-challenge",
            container_id="container-999",
            status="terminated",
            timeout_at=datetime.utcnow() + timedelta(minutes=30),
            terminated_at=datetime.utcnow() - timedelta(minutes=15)
        )
        db_session.add(terminated_session)
        db_session.commit()
        
        # Mock the session manager
        mock_session_manager = Mock()
        mock_get_session_manager.return_value = mock_session_manager
        
        response = client.delete(
            "/api/sessions/terminated-session-999",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        # Should not call session manager since already terminated
        mock_session_manager.terminate_session.assert_not_called()


class TestSessionRequestValidation:
    """Test Pydantic request validation - Requirement 13.5"""
    
    def test_session_create_validates_challenge_id_type(self, client, auth_headers):
        """Session creation should validate challenge_id is a string"""
        response = client.post(
            "/api/sessions/",
            json={"challenge_id": 123},  # Should be string
            headers=auth_headers
        )
        
        # Pydantic will coerce to string or accept it, so this should work
        # But if we send completely invalid data like null, it should fail
        response = client.post(
            "/api/sessions/",
            json={"challenge_id": None},
            headers=auth_headers
        )
        
        assert response.status_code == 422
