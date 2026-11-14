"""
Integration tests for authentication API endpoints.

Tests the complete authentication flow including registration, login, and token validation.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
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


class TestUserRegistration:
    """Test user registration endpoint - Requirement 1.5"""
    
    def test_register_new_user_success(self, client):
        """Registering a new user should succeed"""
        response = client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "password123"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should not be returned
    
    def test_register_duplicate_username(self, client):
        """Registering duplicate username should fail"""
        user_data = {"username": "testuser", "password": "password123"}
        
        # Register first user
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Try to register same username
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
    
    def test_register_invalid_data(self, client):
        """Registering with invalid data should fail"""
        response = client.post(
            "/api/auth/register",
            json={"username": ""}  # Missing password
        )
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login endpoint - Requirements 1.1, 1.2"""
    
    def test_login_valid_credentials(self, client):
        """Login with valid credentials should succeed"""
        # Register user first
        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 0
        assert data["user"]["username"] == "testuser"
        assert "id" in data["user"]
    
    def test_login_invalid_username(self, client):
        """Login with non-existent username should fail within 500ms"""
        import time
        start_time = time.time()
        
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
        assert elapsed_time < 500  # Requirement 1.2: return error within 500ms
    
    def test_login_invalid_password(self, client):
        """Login with incorrect password should fail within 500ms"""
        import time
        
        # Register user first
        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )
        
        start_time = time.time()
        
        # Try to login with wrong password
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        
        elapsed_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
        assert elapsed_time < 500  # Requirement 1.2: return error within 500ms
    
    def test_login_missing_credentials(self, client):
        """Login with missing credentials should fail"""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser"}  # Missing password
        )
        assert response.status_code == 422  # Validation error


class TestGetCurrentUser:
    """Test /me endpoint - Requirements 1.1, 1.3, 1.4"""
    
    def test_get_current_user_with_valid_token(self, client):
        """Accessing /me with valid token should return user info"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "password123"}
        )
        token = login_response.json()["token"]
        
        # Access /me endpoint
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
        assert "created_at" in data
    
    def test_get_current_user_without_token(self, client):
        """Accessing /me without token should fail"""
        response = client.get("/api/auth/me")
        assert response.status_code == 403  # Forbidden without credentials
    
    def test_get_current_user_with_invalid_token(self, client):
        """Accessing /me with invalid token should fail"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401
    
    def test_get_current_user_with_expired_token(self, client):
        """Accessing /me with expired token should fail"""
        # Create an expired token manually
        from app.services.auth_service import create_access_token
        from datetime import timedelta
        
        expired_token = create_access_token(
            {"sub": "123"},
            expires_delta=timedelta(seconds=-1)
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401


class TestAuthenticationFlow:
    """Test complete authentication flow - Requirement 1.1, 1.3"""
    
    def test_complete_auth_flow(self, client):
        """Complete flow: register -> login -> access protected endpoint"""
        # Step 1: Register
        register_response = client.post(
            "/api/auth/register",
            json={"username": "flowtest", "password": "password123"}
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # Step 2: Login
        login_response = client.post(
            "/api/auth/login",
            json={"username": "flowtest", "password": "password123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        assert login_response.json()["user"]["id"] == user_id
        
        # Step 3: Access protected endpoint
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["id"] == user_id
        assert me_response.json()["username"] == "flowtest"
