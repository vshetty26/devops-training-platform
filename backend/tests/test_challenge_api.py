"""
Unit tests for Challenge API Endpoints

Tests the challenge listing and detail endpoints with authentication
and completion status.

Requirements: 2.1, 2.2, 2.3, 2.5
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models import Challenge, User, Attempt
from app.services.auth_service import get_password_hash, create_access_token
import json


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Create test database with tables"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_challenges(db_session):
    """Create sample challenges in database"""
    challenges_data = [
        {
            "id": "nginx-502",
            "title": "Fix Nginx 502 Error",
            "difficulty": "medium",
            "brief": "Nginx is returning 502 errors",
            "metadata": json.dumps({"hints": ["Check upstream config"]})
        },
        {
            "id": "docker-restart",
            "title": "Fix Docker Restart Loop",
            "difficulty": "easy",
            "brief": "Container keeps restarting",
            "metadata": json.dumps({"hints": ["Check logs"]})
        },
        {
            "id": "k8s-crashloop",
            "title": "Fix Kubernetes CrashLoopBackOff",
            "difficulty": "hard",
            "brief": "Pod is in CrashLoopBackOff state",
            "metadata": json.dumps({"hints": ["Check pod logs"]})
        }
    ]
    
    for data in challenges_data:
        challenge = Challenge(**data)
        db_session.add(challenge)
    
    db_session.commit()
    return challenges_data


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        username="testuser",
        password_hash=get_password_hash("testpassword")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Create authentication token for test user"""
    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def completed_attempt(db_session, test_user, sample_challenges):
    """Create a completed attempt for the test user"""
    attempt = Attempt(
        user_id=test_user.id,
        challenge_id="nginx-502",
        session_id="test-session-1",
        success=True,
        completion_time_seconds=300
    )
    db_session.add(attempt)
    db_session.commit()
    return attempt


@pytest.fixture
def multiple_attempts(db_session, test_user, sample_challenges):
    """Create multiple completed attempts for the test user with different times"""
    attempts = [
        Attempt(
            user_id=test_user.id,
            challenge_id="nginx-502",
            session_id="test-session-1",
            success=True,
            completion_time_seconds=500
        ),
        Attempt(
            user_id=test_user.id,
            challenge_id="nginx-502",
            session_id="test-session-2",
            success=True,
            completion_time_seconds=200  # Best time
        ),
        Attempt(
            user_id=test_user.id,
            challenge_id="nginx-502",
            session_id="test-session-3",
            success=True,
            completion_time_seconds=350
        )
    ]
    for attempt in attempts:
        db_session.add(attempt)
    db_session.commit()
    return attempts


class TestChallengeListEndpoint:
    """Tests for GET /api/challenges endpoint"""
    
    def test_list_challenges_unauthenticated(self, client, sample_challenges):
        """Test listing challenges without authentication"""
        response = client.get("/api/challenges/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return all challenges
        assert len(data) == 3
        
        # Verify structure and difficulty tags (Requirement 2.2)
        challenge_ids = [c['id'] for c in data]
        assert "nginx-502" in challenge_ids
        assert "docker-restart" in challenge_ids
        assert "k8s-crashloop" in challenge_ids
        
        # Verify difficulty levels are included
        difficulties = [c['difficulty'] for c in data]
        assert "easy" in difficulties
        assert "medium" in difficulties
        assert "hard" in difficulties
        
        # Verify brief descriptions are included (Requirement 2.3)
        for challenge in data:
            assert 'brief' in challenge
            assert len(challenge['brief']) > 0
        
        # Completion status should be False for unauthenticated users
        for challenge in data:
            assert challenge['completed'] == False
    
    def test_list_challenges_authenticated_no_completions(
        self, client, sample_challenges, auth_token
    ):
        """Test listing challenges when authenticated with no completions"""
        response = client.get(
            "/api/challenges/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        
        # All challenges should be incomplete
        for challenge in data:
            assert challenge['completed'] == False
    
    def test_list_challenges_authenticated_with_completions(
        self, client, sample_challenges, auth_token, completed_attempt
    ):
        """Test listing challenges with completion status (Requirement 2.5)"""
        response = client.get(
            "/api/challenges/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        
        # Find the completed challenge
        nginx_challenge = next(c for c in data if c['id'] == 'nginx-502')
        assert nginx_challenge['completed'] == True
        assert nginx_challenge['completion_time_seconds'] == 300
        
        # Other challenges should be incomplete
        docker_challenge = next(c for c in data if c['id'] == 'docker-restart')
        assert docker_challenge['completed'] == False
        assert docker_challenge['completion_time_seconds'] is None
        
        k8s_challenge = next(c for c in data if c['id'] == 'k8s-crashloop')
        assert k8s_challenge['completed'] == False
        assert k8s_challenge['completion_time_seconds'] is None
    
    def test_list_challenges_returns_best_completion_time(
        self, client, sample_challenges, auth_token, multiple_attempts
    ):
        """Test that the best (fastest) completion time is returned"""
        response = client.get(
            "/api/challenges/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find the challenge with multiple attempts
        nginx_challenge = next(c for c in data if c['id'] == 'nginx-502')
        assert nginx_challenge['completed'] == True
        # Should return the fastest time (200 seconds)
        assert nginx_challenge['completion_time_seconds'] == 200
    
    def test_list_challenges_empty_database(self, client):
        """Test listing challenges when database is empty"""
        response = client.get("/api/challenges/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestChallengeDetailEndpoint:
    """Tests for GET /api/challenges/{id} endpoint"""
    
    def test_get_challenge_detail_unauthenticated(self, client, sample_challenges):
        """Test getting challenge details without authentication"""
        response = client.get("/api/challenges/nginx-502")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify challenge data
        assert data['id'] == 'nginx-502'
        assert data['title'] == 'Fix Nginx 502 Error'
        assert data['difficulty'] == 'medium'
        assert data['brief'] == 'Nginx is returning 502 errors'
        assert data['completed'] == False
    
    def test_get_challenge_detail_authenticated_completed(
        self, client, sample_challenges, auth_token, completed_attempt
    ):
        """Test getting details for completed challenge"""
        response = client.get(
            "/api/challenges/nginx-502",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['id'] == 'nginx-502'
        assert data['completed'] == True
        assert data['completion_time_seconds'] == 300
    
    def test_get_challenge_detail_authenticated_not_completed(
        self, client, sample_challenges, auth_token
    ):
        """Test getting details for uncompleted challenge"""
        response = client.get(
            "/api/challenges/docker-restart",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['id'] == 'docker-restart'
        assert data['completed'] == False
        assert data['completion_time_seconds'] is None
    
    def test_get_challenge_not_found(self, client):
        """Test getting non-existent challenge"""
        response = client.get("/api/challenges/nonexistent-challenge")
        
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data
        assert data['detail'] == "Challenge not found"
    
    def test_get_challenge_with_invalid_auth_token(
        self, client, sample_challenges
    ):
        """Test getting challenge with invalid authentication token"""
        response = client.get(
            "/api/challenges/nginx-502",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        # Should still return challenge data (auth is optional)
        # but completed status should be False
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 'nginx-502'
        assert data['completed'] == False


class TestChallengeDataStructure:
    """Tests for challenge response data structure"""
    
    def test_challenge_response_structure(self, client, sample_challenges):
        """Test that challenge responses have correct structure"""
        response = client.get("/api/challenges/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify each challenge has required fields
        for challenge in data:
            assert 'id' in challenge
            assert 'title' in challenge
            assert 'difficulty' in challenge
            assert 'brief' in challenge
            assert 'completed' in challenge
            assert 'completion_time_seconds' in challenge
            
            # Verify field types
            assert isinstance(challenge['id'], str)
            assert isinstance(challenge['title'], str)
            assert isinstance(challenge['difficulty'], str)
            assert isinstance(challenge['brief'], str)
            assert isinstance(challenge['completed'], bool)
            assert challenge['completion_time_seconds'] is None or isinstance(challenge['completion_time_seconds'], int)
