"""
Session Manager Service

Handles Docker container lifecycle for challenge sessions.

Requirements: 3.1-3.7, 5.1-5.3, 11.1-11.4, 14.1-14.5
"""
import docker
import uuid
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession
from docker.errors import DockerException, NotFound, APIError

from app.models.session import Session

logger = logging.getLogger(__name__)

# Session timeout in minutes (Requirement 5.1)
SESSION_TIMEOUT_MINUTES = 30

class SessionManager:
    """
    Manages challenge session containers.
    
    Responsibilities:
    - Create and configure Docker containers with security constraints
    - Track active sessions
    - Enforce timeout limits
    - Clean up container resources
    
    Requirements:
    - 3.1: Provision Docker container within 10 seconds
    - 3.2: Inject challenge-specific fault via setup.sh
    - 3.3: Enforce 0.5 CPU core limit
    - 3.4: Enforce 256MB memory limit
    - 3.5: Block network egress
    - 3.6: Run as non-root user
    - 3.7: Drop unnecessary Linux capabilities
    - 11.1: Read-only filesystem where permitted
    - 11.2: Prevent Docker socket access
    - 11.3: Prevent host filesystem access
    - 11.4: Apply resource quotas
    - 14.1: Use Docker SDK for Python
    - 14.2: Track active containers
    """
    
    def __init__(self):
        """Initialize Session Manager with Docker client and in-memory tracker."""
        try:
            self.client = docker.from_env()
            # Verify Docker connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise
        
        # In-memory tracker: {session_id: Session object} (Requirement 14.2)
        self.active_sessions: Dict[str, Session] = {}
    
    def create_session(
        self,
        user_id: int,
        challenge_id: str,
        challenge_image: str,
        db: DBSession,
        read_only_fs: bool = False
    ) -> Session:
        """
        Create a new challenge session with isolated container.
        
        Requirements:
        - 3.1: Provision container within 10 seconds
        - 3.2: Execute setup.sh to inject fault
        - 3.3-3.7: Apply security constraints
        - 11.1-11.4: Additional security measures
        
        Args:
            user_id: User attempting the challenge
            challenge_id: Challenge identifier
            challenge_image: Docker image for the challenge
            db: Database session for persisting session metadata
            read_only_fs: Whether to mount root filesystem as read-only (Requirement 11.1)
            
        Returns:
            Session object with session_id, container_id, timeout_at
            
        Raises:
            DockerException: If container creation fails
        """
        session_id = str(uuid.uuid4())
        timeout_at = datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        
        logger.info(f"Creating session {session_id} for user {user_id}, challenge {challenge_id}")
        
        try:
            # Pull or verify image exists (Requirement 3.1)
            try:
                self.client.images.get(challenge_image)
                logger.info(f"Using existing image: {challenge_image}")
            except NotFound:
                logger.info(f"Pulling image: {challenge_image}")
                self.client.images.pull(challenge_image)
            
            # Create container with security constraints (Requirements 3.3-3.7, 11.1-11.4)
            container = self.client.containers.create(
                image=challenge_image,
                
                # Requirement 3.6: Run as non-root user (UID 1000)
                user="1000:1000",
                
                # Requirement 3.5: Block all network egress
                network_mode="none",
                
                # Requirement 3.4: Enforce 256MB memory limit
                mem_limit="256m",
                
                # Requirement 3.3: Enforce 0.5 CPU cores
                # cpu_period defines the period (100ms default)
                # cpu_quota defines how much of that period this container can use
                # 50000/100000 = 0.5 cores
                cpu_period=100000,
                cpu_quota=50000,
                
                # Requirement 3.7: Drop all unnecessary Linux capabilities
                # Only keep minimal capabilities needed for basic operations
                cap_drop=["ALL"],
                cap_add=[
                    "CHOWN",           # Change file ownership
                    "DAC_OVERRIDE",    # Bypass file permission checks
                    "FOWNER",          # Bypass permission checks for operations that require file ownership
                    "SETGID",          # Set group ID
                    "SETUID",          # Set user ID
                    "NET_BIND_SERVICE" # Bind to privileged ports (<1024)
                ],
                
                # Requirement 11.1: Read-only root filesystem (where challenge permits)
                read_only=read_only_fs,
                
                # Requirement 11.2: Prevent Docker socket access (no volumes mounted)
                # Requirement 11.3: Prevent host filesystem access (no host mounts)
                volumes=None,
                
                # Additional security: Prevent privilege escalation
                security_opt=["no-new-privileges:true"],
                
                # Keep container running for terminal access
                detach=True,
                tty=True,
                stdin_open=True,
                
                # Use bash as entry point for terminal sessions
                command="/bin/bash",
                
                # Label for tracking
                labels={
                    "devops_arena.session_id": session_id,
                    "devops_arena.user_id": str(user_id),
                    "devops_arena.challenge_id": challenge_id
                }
            )
            
            # Start the container (Requirement 14.1)
            container.start()
            
            # Log container started (INFO level - container lifecycle event)
            logger.info(
                f"Container started - session_id: {session_id}, container_id: {container.id}, "
                f"user_id: {user_id}, challenge_id: {challenge_id}"
            )
            
            # Requirement 3.2: Execute setup.sh script to inject fault
            try:
                setup_result = container.exec_run(
                    cmd="/bin/bash /challenge/setup.sh",
                    user="1000:1000",
                    workdir="/challenge"
                )
                
                if setup_result.exit_code != 0:
                    logger.warning(
                        f"Setup script failed for session {session_id}: "
                        f"{setup_result.output.decode('utf-8', errors='ignore')}"
                    )
                else:
                    logger.info(f"Setup script executed successfully for session {session_id}")
                    
            except APIError as e:
                logger.error(f"Failed to execute setup script for session {session_id}: {e}")
                # Continue anyway - some challenges might not need setup
            
            # Create session database record (Requirement 10.3)
            db_session = Session(
                id=session_id,
                user_id=user_id,
                challenge_id=challenge_id,
                container_id=container.id,
                status="active",
                timeout_at=timeout_at
            )
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            
            # Store in in-memory tracker (Requirement 14.2)
            self.active_sessions[session_id] = db_session
            
            # Log session created successfully (INFO level - container lifecycle event)
            logger.info(
                f"Session created - session_id: {session_id}, container_id: {container.id}, "
                f"user_id: {user_id}, challenge_id: {challenge_id}, timeout_at: {timeout_at.isoformat()}"
            )
            
            return db_session
            
        except DockerException as e:
            logger.error(f"Docker error creating session {session_id}: {e}")
            # Clean up on failure
            try:
                if 'container' in locals():
                    container.remove(force=True)
            except:
                pass
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating session {session_id}: {e}")
            # Clean up on failure
            try:
                if 'container' in locals():
                    container.remove(force=True)
            except:
                pass
            raise
    
    def terminate_session(self, session_id: str, db: DBSession) -> None:
        """
        Terminate a session and clean up container resources.
        
        Requirements:
        - 14.3: Remove container within 5 seconds of session end
        - 14.5: Track active containers and prevent resource leaks
        
        Args:
            session_id: Session to terminate
            db: Database session for updating session status
            
        Raises:
            ValueError: If session not found
        """
        logger.info(f"Terminating session {session_id}")
        
        # Retrieve session from database
        db_session = db.query(Session).filter(Session.id == session_id).first()
        if not db_session:
            logger.warning(f"Session {session_id} not found in database")
            raise ValueError(f"Session {session_id} not found")
        
        try:
            # Get container
            container = self.client.containers.get(db_session.container_id)
            
            # Stop container gracefully (10s timeout)
            logger.info(
                f"Stopping container - session_id: {session_id}, container_id: {db_session.container_id}"
            )
            container.stop(timeout=10)
            
            # Remove container (Requirement 14.3)
            logger.info(
                f"Removing container - session_id: {session_id}, container_id: {db_session.container_id}"
            )
            container.remove()
            
            # Log container removed (INFO level - container lifecycle event)
            logger.info(
                f"Container removed - session_id: {session_id}, container_id: {db_session.container_id}, "
                f"user_id: {db_session.user_id}, challenge_id: {db_session.challenge_id}"
            )
            
        except NotFound:
            logger.warning(f"Container {db_session.container_id} not found, may already be removed")
        except APIError as e:
            logger.error(f"Docker API error terminating session {session_id}: {e}")
            # Try force removal
            try:
                container = self.client.containers.get(db_session.container_id)
                container.remove(force=True)
                logger.info(f"Force removed container {db_session.container_id}")
            except:
                logger.error(f"Failed to force remove container {db_session.container_id}")
        
        # Update database (Requirement 10.3)
        db_session.status = "terminated"
        db_session.terminated_at = datetime.utcnow()
        db.commit()
        
        # Remove from in-memory tracker (Requirement 14.5)
        self.active_sessions.pop(session_id, None)
        
        # Log session terminated (INFO level - normal operation)
        logger.info(
            f"Session terminated - session_id: {session_id}, "
            f"user_id: {db_session.user_id}, challenge_id: {db_session.challenge_id}"
        )
    
    def enforce_timeout(self, session_id: str, db: DBSession) -> None:
        """
        Forcefully stop and remove a timed-out container.
        
        Requirements:
        - 5.2: Terminate container when countdown reaches zero
        - 5.3: Remove all container resources after termination
        - 14.4: Forcefully stop and remove on timeout
        
        Args:
            session_id: Session that timed out
            db: Database session for updating session status
        """
        logger.warning(f"Enforcing timeout for session {session_id}")
        
        # Retrieve session from database
        db_session = db.query(Session).filter(Session.id == session_id).first()
        if not db_session:
            logger.warning(f"Session {session_id} not found in database")
            return
        
        try:
            # Get container and force remove
            container = self.client.containers.get(db_session.container_id)
            
            logger.info(
                f"Force removing timed-out container - session_id: {session_id}, "
                f"container_id: {db_session.container_id}"
            )
            container.remove(force=True)
            
            # Log container removed due to timeout (WARNING level - timeout event)
            logger.warning(
                f"Container removed due to timeout - session_id: {session_id}, "
                f"container_id: {db_session.container_id}, user_id: {db_session.user_id}, "
                f"challenge_id: {db_session.challenge_id}"
            )
            
        except NotFound:
            logger.warning(f"Container {db_session.container_id} not found, may already be removed")
        except APIError as e:
            logger.error(f"Docker API error enforcing timeout for session {session_id}: {e}")
        
        # Update database with timeout status (Requirement 5.3)
        db_session.status = "timeout"
        db_session.terminated_at = datetime.utcnow()
        db.commit()
        
        # Remove from in-memory tracker (Requirement 14.5)
        self.active_sessions.pop(session_id, None)
        
        logger.info(f"Timeout enforced for session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session from in-memory tracker.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object or None if not found
        """
        return self.active_sessions.get(session_id)
    
    def cleanup_stale_sessions(self, db: DBSession) -> None:
        """
        Clean up sessions that have exceeded their timeout.
        
        Should be called periodically by a background task.
        
        Args:
            db: Database session for querying and updating sessions
        """
        now = datetime.utcnow()
        
        # Find all active sessions that have timed out
        timed_out_sessions = db.query(Session).filter(
            Session.status == "active",
            Session.timeout_at <= now
        ).all()
        
        logger.info(f"Found {len(timed_out_sessions)} timed-out sessions to clean up")
        
        for session in timed_out_sessions:
            try:
                self.enforce_timeout(session.id, db)
            except Exception as e:
                logger.error(f"Error cleaning up session {session.id}: {e}")
