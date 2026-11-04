"""
Unit tests for SQLAlchemy models.

Requirements: 10.1, 10.5
"""
import pytest
from datetime import datetime
from app.models import User, Challenge, Session, Attempt

def test_user_model():
    """Test User model creation"""
    user = User(
        username="testuser",
        password_hash="hashed_password"
    )
    assert user.username == "testuser"
    assert user.password_hash == "hashed_password"

def test_challenge_model():
    """Test Challenge model creation"""
    challenge = Challenge(
        id="test-challenge",
        title="Test Challenge",
        difficulty="medium",
        brief="Test brief",
        metadata='{"hints": []}'
    )
    assert challenge.id == "test-challenge"
    assert challenge.title == "Test Challenge"
    assert challenge.difficulty == "medium"

def test_session_model():
    """Test Session model creation"""
    session = Session(
        id="session-123",
        user_id=1,
        challenge_id="test-challenge",
        container_id="container-123",
        status="active",
        timeout_at=datetime.now()
    )
    assert session.id == "session-123"
    assert session.status == "active"

def test_attempt_model():
    """Test Attempt model creation"""
    attempt = Attempt(
        user_id=1,
        challenge_id="test-challenge",
        session_id="session-123",
        success=True,
        completion_time_seconds=300
    )
    assert attempt.success is True
    assert attempt.completion_time_seconds == 300
