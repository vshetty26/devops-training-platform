"""
Tests for validation API endpoint.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.main import app
from app.database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.challenge import Challenge
from app.models.session import Session as SessionModel
from app.models.attempt import Attempt
from app.services.auth_service import create_access_token

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_validation.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    """Create test database tables before each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_user(setup_database):
    """Create a test user."""
    db = TestingSessionLocal()
    user = User(username="testuser", password_hash="hashed_password")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def test_challenge(setup_database):
    """Create a test challenge."""
    db = TestingSessionLocal()
    challenge = Challenge(
        id="nginx-502",
        title="Fix Nginx 502",
        difficulty="medium",
        brief="Fix the broken Nginx configuration"
    )
    db.add(challenge)
    db.commit()
    challenge_id = challenge.id
    db.close()
    return {"id": challenge_id}

@pytest.fixture
def test_session(test_user, test_challenge):
    """Create a test session."""
    db = TestingSessionLocal()
    session = SessionModel(
        id="test-session-123",
        user_id=test_user.id,
        challenge_id=test_challenge["id"],
        container_id="test-container-456",
        status="active",
        timeout_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.add(session)
    db.commit()
    session_id = session.id
    db.close()
    
    # Return a dict with session info instead of detached object
    return {"id": session_id, "user_id": test_user.id, "challenge_id": test_challenge["id"]}

@pytest.fixture
def auth_token(test_user):
    """Create an authentication token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})

def test_validate_solution_success(test_session, auth_token):
    """
    Test successful validation.
    
    Requirements: 6.1, 6.2, 6.5, 6.6
    """
    session_id = test_session["id"]
    
    # Mock Docker client and container
    with patch('app.routers.sessions.get_session_manager') as mock_get_manager:
        mock_manager = Mock()
        mock_container = Mock()
        mock_client = Mock()
        
        # Mock successful validation script execution (exit code 0)
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.output = b"Success! Nginx is returning HTTP 200 OK"
        mock_container.exec_run.return_value = mock_result
        
        mock_client.containers.get.return_value = mock_container
        mock_manager.client = mock_client
        mock_get_manager.return_value = mock_manager
        
        # Make validation request
        response = client.post(
            f"/api/sessions/{session_id}/validate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Success" in data["message"]
        assert data["hint"] is None
        
        # Verify Docker exec was called correctly (Requirement 6.1)
        mock_container.exec_run.assert_called_once_with(
            cmd="/bin/bash /challenge/validate.sh",
            user="1000:1000",
            workdir="/challenge"
        )
        
        # Verify attempt was recorded in database (Requirement 6.6)
        db = TestingSessionLocal()
        attempt = db.query(Attempt).filter(
            Attempt.session_id == session_id
        ).first()
        assert attempt is not None
        assert attempt.success is True
        assert attempt.completion_time_seconds is not None
        assert attempt.completion_time_seconds >= 0
        
        # Verify session status was updated
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        assert session.status == "completed"
        assert session.terminated_at is not None
        db.close()

def test_validate_solution_failure(test_session, auth_token):
    """
    Test failed validation with hint.
    
    Requirements: 6.1, 6.3, 6.4
    """
    session_id = test_session["id"]
    
    # Mock Docker client and container
    with patch('app.routers.sessions.get_session_manager') as mock_get_manager:
        mock_manager = Mock()
        mock_container = Mock()
        mock_client = Mock()
        
        # Mock failed validation script execution (exit code 1)
        mock_result = Mock()
        mock_result.exit_code = 1
        mock_result.output = b"Validation failed: Nginx returned HTTP 502\n\nHint: Check the Nginx configuration files and error logs"
        mock_container.exec_run.return_value = mock_result
        
        mock_client.containers.get.return_value = mock_container
        mock_manager.client = mock_client
        mock_get_manager.return_value = mock_manager
        
        # Make validation request
        response = client.post(
            f"/api/sessions/{session_id}/validate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Assert response (Requirement 6.3)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed" in data["message"].lower() or "Validation failed" in data["message"]
        
        # Verify hint is provided (Requirement 6.4)
        assert data["hint"] is not None
        assert "Check the Nginx configuration" in data["hint"]
        
        # Verify Docker exec was called correctly (Requirement 6.1)
        mock_container.exec_run.assert_called_once()
        
        # Verify failed attempt was recorded in database
        db = TestingSessionLocal()
        attempt = db.query(Attempt).filter(
            Attempt.session_id == session_id
        ).first()
        assert attempt is not None
        assert attempt.success is False
        assert attempt.completion_time_seconds is None
        db.close()

def test_validate_solution_session_not_found(auth_token):
    """Test validation with non-existent session."""
    response = client.post(
        "/api/sessions/nonexistent-session/validate",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_validate_solution_wrong_user(test_session, setup_database):
    """Test validation when user doesn't own the session."""
    session_id = test_session["id"]
    
    # Create a different user
    db = TestingSessionLocal()
    other_user = User(username="otheruser", password_hash="hashed_password")
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    db.close()
    
    # Create token for the other user
    other_token = create_access_token(data={"sub": str(other_user.id)})
    
    # Try to validate with wrong user
    response = client.post(
        f"/api/sessions/{session_id}/validate",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()

def test_validate_solution_inactive_session(test_session, auth_token):
    """Test validation when session is not active."""
    session_id = test_session["id"]
    
    # Update session status to completed
    db = TestingSessionLocal()
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    session.status = "completed"
    db.commit()
    db.close()
    
    # Try to validate
    response = client.post(
        f"/api/sessions/{session_id}/validate",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "completed" in response.json()["detail"].lower()

def test_validate_solution_container_not_found(test_session, auth_token):
    """Test validation when container doesn't exist."""
    session_id = test_session["id"]
    
    # Mock Docker client to raise NotFound error
    with patch('app.routers.sessions.get_session_manager') as mock_get_manager:
        mock_manager = Mock()
        mock_client = Mock()
        
        import docker
        mock_client.containers.get.side_effect = docker.errors.NotFound("Container not found")
        
        mock_manager.client = mock_client
        mock_get_manager.return_value = mock_manager
        
        # Make validation request
        response = client.post(
            f"/api/sessions/{session_id}/validate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Assert error response
        assert response.status_code == 500
        assert "not found" in response.json()["detail"].lower()

def test_validate_solution_completion_time_calculation(test_session, auth_token):
    """
    Test that completion time is correctly calculated.
    
    Requirement: 6.5
    """
    session_id = test_session["id"]
    
    # Set session created_at to a specific time
    db = TestingSessionLocal()
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    session.created_at = datetime.utcnow() - timedelta(seconds=120)  # 2 minutes ago
    db.commit()
    db.close()
    
    # Mock Docker client and container
    with patch('app.routers.sessions.get_session_manager') as mock_get_manager:
        mock_manager = Mock()
        mock_container = Mock()
        mock_client = Mock()
        
        # Mock successful validation
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.output = b"Success!"
        mock_container.exec_run.return_value = mock_result
        
        mock_client.containers.get.return_value = mock_container
        mock_manager.client = mock_client
        mock_get_manager.return_value = mock_manager
        
        # Make validation request
        response = client.post(
            f"/api/sessions/{session_id}/validate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify completion time was calculated (Requirement 6.5)
        db = TestingSessionLocal()
        attempt = db.query(Attempt).filter(
            Attempt.session_id == session_id
        ).first()
        assert attempt is not None
        assert attempt.completion_time_seconds is not None
        # Should be approximately 120 seconds (allow some margin)
        assert 115 <= attempt.completion_time_seconds <= 125
        db.close()

def test_validate_solution_unauthenticated():
    """Test validation without authentication token."""
    response = client.post("/api/sessions/test-session/validate")
    
    assert response.status_code == 401
