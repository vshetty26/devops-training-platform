"""
Unit tests for Session Manager Service

Tests Requirements: 17.1-17.5
- 17.1: Unit tests for session creation logic
- 17.2: Unit tests for session termination logic
- 17.3: Unit tests for timeout enforcement
- 17.4: Unit tests for resource limit configuration
- 17.5: Verify tests pass before deployment
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from docker.errors import NotFound, APIError

from app.services.session_manager import SessionManager, SESSION_TIMEOUT_MINUTES
from app.models.session import Session


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing without actual Docker operations."""
    with patch('app.services.session_manager.docker.from_env') as mock_docker:
        client = MagicMock()
        mock_docker.return_value = client
        
        # Mock ping to verify connection
        client.ping.return_value = True
        
        yield client


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.fixture
def session_manager(mock_docker_client):
    """Create SessionManager instance with mocked Docker client."""
    return SessionManager()


class TestSessionManagerInit:
    """Test SessionManager initialization."""
    
    def test_init_successful(self, mock_docker_client):
        """Test successful SessionManager initialization."""
        manager = SessionManager()
        
        assert manager.client is not None
        assert manager.active_sessions == {}
        mock_docker_client.ping.assert_called_once()
    
    def test_init_docker_connection_failure(self):
        """Test initialization failure when Docker is unreachable."""
        with patch('app.services.session_manager.docker.from_env') as mock_docker:
            mock_docker.side_effect = Exception("Docker not available")
            
            with pytest.raises(Exception, match="Docker not available"):
                SessionManager()


class TestCreateSession:
    """Test create_session method (Requirement 17.1)."""
    
    def test_create_session_success(self, session_manager, mock_docker_client, mock_db_session):
        """Test successful session creation with all security constraints."""
        # Setup
        user_id = 1
        challenge_id = "nginx-502"
        challenge_image = "devops-arena/nginx-502:latest"
        
        # Mock image exists
        mock_docker_client.images.get.return_value = MagicMock()
        
        # Mock container creation
        mock_container = MagicMock()
        mock_container.id = "container_123"
        mock_docker_client.containers.create.return_value = mock_container
        
        # Mock setup script execution
        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"Setup complete")
        
        # Execute
        result = session_manager.create_session(
            user_id=user_id,
            challenge_id=challenge_id,
            challenge_image=challenge_image,
            db=mock_db_session,
            read_only_fs=False
        )
        
        # Verify
        assert result is not None
        assert result.user_id == user_id
        assert result.challenge_id == challenge_id
        assert result.container_id == "container_123"
        assert result.status == "active"
        
        # Verify Docker container created with correct security constraints
        create_call = mock_docker_client.containers.create.call_args
        assert create_call.kwargs['image'] == challenge_image
        
        # Requirement 3.6: Non-root user
        assert create_call.kwargs['user'] == "1000:1000"
        
        # Requirement 3.5: Network isolation
        assert create_call.kwargs['network_mode'] == "none"
        
        # Requirement 3.4: Memory limit
        assert create_call.kwargs['mem_limit'] == "256m"
        
        # Requirement 3.3: CPU limit (0.5 cores)
        assert create_call.kwargs['cpu_period'] == 100000
        assert create_call.kwargs['cpu_quota'] == 50000
        
        # Requirement 3.7: Dropped capabilities
        assert create_call.kwargs['cap_drop'] == ["ALL"]
        assert "CHOWN" in create_call.kwargs['cap_add']
        assert "SETUID" in create_call.kwargs['cap_add']
        
        # Requirement 11.2, 11.3: No volumes
        assert create_call.kwargs['volumes'] is None
        
        # Verify container started
        mock_container.start.assert_called_once()
        
        # Requirement 3.2: Setup script executed
        mock_container.exec_run.assert_called_once()
        exec_call = mock_container.exec_run.call_args
        assert "/challenge/setup.sh" in exec_call.kwargs['cmd']
        
        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called()
        
        # Verify in-memory tracking (Requirement 14.2)
        assert result.id in session_manager.active_sessions
    
    def test_create_session_with_readonly_filesystem(self, session_manager, mock_docker_client, mock_db_session):
        """Test session creation with read-only filesystem (Requirement 11.1)."""
        # Setup
        mock_docker_client.images.get.return_value = MagicMock()
        mock_container = MagicMock()
        mock_container.id = "container_123"
        mock_docker_client.containers.create.return_value = mock_container
        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"")
        
        # Execute with read_only_fs=True
        session_manager.create_session(
            user_id=1,
            challenge_id="test",
            challenge_image="test:latest",
            db=mock_db_session,
            read_only_fs=True
        )
        
        # Verify read_only flag set
        create_call = mock_docker_client.containers.create.call_args
        assert create_call.kwargs['read_only'] is True
    
    def test_create_session_pulls_missing_image(self, session_manager, mock_docker_client, mock_db_session):
        """Test that missing images are pulled before container creation."""
        # Setup - image not found initially
        mock_docker_client.images.get.side_effect = NotFound("Image not found")
        mock_docker_client.images.pull.return_value = MagicMock()
        
        mock_container = MagicMock()
        mock_container.id = "container_123"
        mock_docker_client.containers.create.return_value = mock_container
        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"")
        
        # Execute
        session_manager.create_session(
            user_id=1,
            challenge_id="test",
            challenge_image="test:latest",
            db=mock_db_session
        )
        
        # Verify image was pulled
        mock_docker_client.images.pull.assert_called_once_with("test:latest")
    
    def test_create_session_setup_script_failure(self, session_manager, mock_docker_client, mock_db_session):
        """Test session creation continues even if setup script fails."""
        # Setup
        mock_docker_client.images.get.return_value = MagicMock()
        mock_container = MagicMock()
        mock_container.id = "container_123"
        mock_docker_client.containers.create.return_value = mock_container
        
        # Setup script fails
        mock_container.exec_run.return_value = MagicMock(
            exit_code=1,
            output=b"Setup failed"
        )
        
        # Execute - should not raise exception
        result = session_manager.create_session(
            user_id=1,
            challenge_id="test",
            challenge_image="test:latest",
            db=mock_db_session
        )
        
        # Verify session still created
        assert result is not None
        assert result.status == "active"
    
    def test_create_session_container_creation_failure(self, session_manager, mock_docker_client, mock_db_session):
        """Test that container creation failure is handled properly."""
        # Setup
        mock_docker_client.images.get.return_value = MagicMock()
        mock_docker_client.containers.create.side_effect = APIError("Container creation failed")
        
        # Execute - should raise exception
        with pytest.raises(APIError):
            session_manager.create_session(
                user_id=1,
                challenge_id="test",
                challenge_image="test:latest",
                db=mock_db_session
            )
        
        # Verify no database commit occurred
        mock_db_session.commit.assert_not_called()
    
    def test_create_session_timeout_calculation(self, session_manager, mock_docker_client, mock_db_session):
        """Test that session timeout is calculated correctly (Requirement 5.1)."""
        # Setup
        mock_docker_client.images.get.return_value = MagicMock()
        mock_container = MagicMock()
        mock_container.id = "container_123"
        mock_docker_client.containers.create.return_value = mock_container
        mock_container.exec_run.return_value = MagicMock(exit_code=0, output=b"")
        
        # Execute
        before_creation = datetime.utcnow()
        result = session_manager.create_session(
            user_id=1,
            challenge_id="test",
            challenge_image="test:latest",
            db=mock_db_session
        )
        after_creation = datetime.utcnow()
        
        # Verify timeout is approximately 30 minutes from now
        expected_timeout_min = before_creation + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        expected_timeout_max = after_creation + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        
        assert result.timeout_at >= expected_timeout_min
        assert result.timeout_at <= expected_timeout_max


class TestTerminateSession:
    """Test terminate_session method (Requirement 17.2)."""
    
    def test_terminate_session_success(self, session_manager, mock_docker_client, mock_db_session):
        """Test successful session termination."""
        # Setup
        session_id = str(uuid.uuid4())
        container_id = "container_123"
        
        # Mock database session
        db_session_obj = Session(
            id=session_id,
            user_id=1,
            challenge_id="test",
            container_id=container_id,
            status="active",
            timeout_at=datetime.utcnow() + timedelta(minutes=30)
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = db_session_obj
        
        # Mock container
        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container
        
        # Add to in-memory tracker
        session_manager.active_sessions[session_id] = db_session_obj
        
        # Execute
        session_manager.terminate_session(session_id, mock_db_session)
        
        # Verify
        mock_container.stop.assert_called_once_with(timeout=10)
        mock_container.remove.assert_called_once()
        
        # Verify database updated
        assert db_session_obj.status == "terminated"
        assert db_session_obj.terminated_at is not None
        mock_db_session.commit.assert_called()
        
        # Verify removed from in-memory tracker (Requirement 14.5)
        assert session_id not in session_manager.active_sessions
    
    def test_terminate_session_not_found(self, session_manager, mock_docker_client, mock_db_session):
        """Test termination of non-existent session."""
        # Setup - session not in database
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute - should raise ValueError
        with pytest.raises(ValueError, match="not found"):
            session_manager.terminate_session("nonexistent_id", mock_db_session)
    
    def test_terminate_session_container_already_removed(self, session_manager, mock_docker_client, mock_db_session):
        """Test termination when container is already removed."""
        # Setup
        session_id = str(uuid.uuid4())
        db_session_obj = Session(
            id=session_id,
            user_id=1,
            challenge_id="test",
            container_id="container_123",
            status="active",
            timeout_at=datetime.utcnow() + timedelta(minutes=30)
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = db_session_obj
        
        # Container not found
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")
        
        # Execute - should not raise exception
        session_manager.terminate_session(session_id, mock_db_session)
        
        # Verify database still updated
        assert db_session_obj.status == "terminated"
        mock_db_session.commit.assert_called()
    
    def test_terminate_session_force_removal_on_api_error(self, session_manager, mock_docker_client, mock_db_session):
        """Test force removal when normal termination fails."""
        # Setup
        session_id = str(uuid.uuid4())
        db_session_obj = Session(
            id=session_id,
            user_id=1,
            challenge_id="test",
            container_id="container_123",
            status="active",
            timeout_at=datetime.utcnow() + timedelta(minutes=30)
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = db_session_obj
        
        # Mock container - stop fails, but force remove succeeds
        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container
        mock_container.stop.side_effect = APIError("Stop failed")
        
        # Execute
        session_manager.terminate_session(session_id, mock_db_session)
        
        # Verify force remove attempted
        mock_container.remove.assert_called()


class TestEnforceTimeout:
    """Test enforce_timeout method (Requirement 17.3)."""
    
    def test_enforce_timeout_success(self, session_manager, mock_docker_client, mock_db_session):
        """Test successful timeout enforcement (Requirement 5.2, 5.3)."""
        # Setup
        session_id = str(uuid.uuid4())
        db_session_obj = Session(
            id=session_id,
            user_id=1,
            challenge_id="test",
            container_id="container_123",
            status="active",
            timeout_at=datetime.utcnow() - timedelta(minutes=1)  # Already timed out
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = db_session_obj
        
        # Mock container
        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container
        
        # Add to in-memory tracker
        session_manager.active_sessions[session_id] = db_session_obj
        
        # Execute
        session_manager.enforce_timeout(session_id, mock_db_session)
        
        # Verify force removal (Requirement 14.4)
        mock_container.remove.assert_called_once_with(force=True)
        
        # Verify database updated with timeout status
        assert db_session_obj.status == "timeout"
        assert db_session_obj.terminated_at is not None
        mock_db_session.commit.assert_called()
        
        # Verify removed from in-memory tracker
        assert session_id not in session_manager.active_sessions
    
    def test_enforce_timeout_container_not_found(self, session_manager, mock_docker_client, mock_db_session):
        """Test timeout enforcement when container is already gone."""
        # Setup
        session_id = str(uuid.uuid4())
        db_session_obj = Session(
            id=session_id,
            user_id=1,
            challenge_id="test",
            container_id="container_123",
            status="active",
            timeout_at=datetime.utcnow() - timedelta(minutes=1)
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = db_session_obj
        
        # Container not found
        mock_docker_client.containers.get.side_effect = NotFound("Container not found")
        
        # Execute - should not raise exception
        session_manager.enforce_timeout(session_id, mock_db_session)
        
        # Verify database still updated
        assert db_session_obj.status == "timeout"
        mock_db_session.commit.assert_called()
    
    def test_enforce_timeout_session_not_found(self, session_manager, mock_docker_client, mock_db_session):
        """Test timeout enforcement with non-existent session."""
        # Setup - session not in database
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute - should not raise exception
        session_manager.enforce_timeout("nonexistent_id", mock_db_session)
        
        # Verify no container operations attempted
        mock_docker_client.containers.get.assert_not_called()


class TestGetSession:
    """Test get_session method."""
    
    def test_get_session_exists(self, session_manager):
        """Test retrieving existing session from in-memory tracker."""
        # Setup
        session_id = str(uuid.uuid4())
        session_obj = Session(
            id=session_id,
            user_id=1,
            challenge_id="test",
            container_id="container_123",
            status="active",
            timeout_at=datetime.utcnow() + timedelta(minutes=30)
        )
        session_manager.active_sessions[session_id] = session_obj
        
        # Execute
        result = session_manager.get_session(session_id)
        
        # Verify
        assert result == session_obj
    
    def test_get_session_not_found(self, session_manager):
        """Test retrieving non-existent session returns None."""
        result = session_manager.get_session("nonexistent_id")
        assert result is None


class TestCleanupStaleSessions:
    """Test cleanup_stale_sessions method."""
    
    def test_cleanup_stale_sessions(self, session_manager, mock_docker_client, mock_db_session):
        """Test cleanup of multiple timed-out sessions."""
        # Setup - create 2 timed-out sessions
        session1 = Session(
            id=str(uuid.uuid4()),
            user_id=1,
            challenge_id="test1",
            container_id="container_1",
            status="active",
            timeout_at=datetime.utcnow() - timedelta(minutes=5)
        )
        session2 = Session(
            id=str(uuid.uuid4()),
            user_id=2,
            challenge_id="test2",
            container_id="container_2",
            status="active",
            timeout_at=datetime.utcnow() - timedelta(minutes=10)
        )
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [session1, session2]
        
        # Mock container operations for enforce_timeout
        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container
        
        # Mock individual session queries for enforce_timeout
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [session1, session2]
        
        # Execute
        session_manager.cleanup_stale_sessions(mock_db_session)
        
        # Verify both sessions were processed
        assert mock_container.remove.call_count == 2
        assert session1.status == "timeout"
        assert session2.status == "timeout"
    
    def test_cleanup_stale_sessions_none_found(self, session_manager, mock_db_session):
        """Test cleanup when no timed-out sessions exist."""
        # Setup - no timed-out sessions
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        # Execute - should not raise exception
        session_manager.cleanup_stale_sessions(mock_db_session)
        
        # Verify no container operations
        session_manager.client.containers.get.assert_not_called()
