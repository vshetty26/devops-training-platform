from fastapi import APIRouter, Depends, WebSocket, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SessionCreateRequest, SessionResponse, ValidationResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.models.challenge import Challenge
from app.services.session_manager import SessionManager
import logging
import docker

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy initialization of session manager to avoid Docker connection during import
_session_manager = None

def get_session_manager() -> SessionManager:
    """
    Get or create the session manager singleton.
    
    This lazy initialization approach prevents Docker connection attempts
    during module import, which is important for testing.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new challenge session with isolated container.
    
    This endpoint provisions a Docker container for the specified challenge,
    applies security constraints, and returns session details including the
    WebSocket URL for terminal connection.
    
    Requirements: 
    - 3.1: Provision Docker container within 10 seconds
    - 5.1: Start 30-minute countdown timer
    - 13.5: Validate request with Pydantic models
    
    Args:
        request: Session creation request with challenge_id
        db: Database session
        current_user: Authenticated user from JWT token
        
    Returns:
        SessionResponse with session_id, container_id, websocket_url, timeout_seconds
        
    Raises:
        HTTPException 404: Challenge not found
        HTTPException 503: Container creation failed
    """
    logger.info(f"User {current_user.id} requesting new session for challenge {request.challenge_id}")
    
    # Validate challenge exists
    challenge = db.query(Challenge).filter(Challenge.id == request.challenge_id).first()
    if not challenge:
        logger.warning(f"Challenge {request.challenge_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge '{request.challenge_id}' not found"
        )
    
    try:
        # Create challenge image name from challenge ID
        challenge_image = f"devops-arena-{request.challenge_id}:latest"
        
        # Get session manager
        session_manager = get_session_manager()
        
        # Create session using session manager (Requirement 3.1)
        session = session_manager.create_session(
            user_id=current_user.id,
            challenge_id=request.challenge_id,
            challenge_image=challenge_image,
            db=db,
            read_only_fs=False  # Can be configured per challenge if needed
        )
        
        # Build WebSocket URL
        websocket_url = f"ws://localhost:8000/api/sessions/{session.id}/terminal"
        
        logger.info(f"Session {session.id} created successfully for user {current_user.id}")
        
        # Return session response (Requirement 13.5)
        return SessionResponse(
            session_id=session.id,
            container_id=session.container_id,
            websocket_url=websocket_url,
            timeout_seconds=30 * 60  # 30 minutes in seconds (Requirement 5.1)
        )
        
    except Exception as e:
        logger.error(f"Failed to create session for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to create session: {str(e)}"
        )

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Terminate an active session and clean up container resources.
    
    This endpoint stops and removes the Docker container associated with
    the session, updates the database, and cleans up in-memory tracking.
    
    Requirements: 
    - 5.2: Terminate container when requested
    - 5.3: Remove all container resources after termination
    - 13.5: Validate request with Pydantic models
    
    Args:
        session_id: Session identifier to terminate
        db: Database session
        current_user: Authenticated user from JWT token
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException 404: Session not found
        HTTPException 403: User does not own this session
        HTTPException 500: Failed to terminate session
    """
    logger.info(f"User {current_user.id} requesting termination of session {session_id}")
    
    # Retrieve session from database
    from app.models.session import Session as SessionModel
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        logger.warning(f"Session {session_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )
    
    # Verify session ownership (Requirement 1.4: restrict access)
    if session.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to terminate session {session_id} "
            f"owned by user {session.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to terminate this session"
        )
    
    # Check if session is already terminated
    if session.status in ["terminated", "timeout", "completed"]:
        logger.info(f"Session {session_id} already terminated with status: {session.status}")
        return  # Return 204 No Content
    
    try:
        # Get session manager
        session_manager = get_session_manager()
        
        # Terminate session using session manager (Requirements 5.2, 5.3)
        session_manager.terminate_session(session_id, db)
        logger.info(f"Session {session_id} terminated successfully")
        return  # Return 204 No Content
        
    except ValueError as e:
        # Session not found (should not happen as we checked above, but handle it)
        logger.error(f"Session {session_id} not found during termination: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to terminate session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to terminate session: {str(e)}"
        )

@router.post("/{session_id}/validate", response_model=ValidationResponse)
async def validate_solution(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate user's solution for a challenge session.
    
    This endpoint executes the challenge-specific validation script inside the
    container and records successful attempts in the database.
    
    Requirements:
    - 6.1: Execute validation script inside container when user clicks check
    - 6.2: Mark attempt as successful when validation script exits with code 0
    - 6.3: Mark attempt as failed when validation script exits with non-zero code
    - 6.4: Display hint message to user when validation fails
    - 6.5: Record completion time from session start to successful validation
    - 6.6: Persist successful attempt to database
    - 11.5: Log validation attempts and results
    
    Args:
        session_id: Session identifier to validate
        db: Database session
        current_user: Authenticated user from JWT token
        
    Returns:
        ValidationResponse with success flag, message, and optional hint
        
    Raises:
        HTTPException 404: Session not found
        HTTPException 403: User does not own this session
        HTTPException 400: Session is not active
        HTTPException 500: Container or validation error
    """
    # Log validation attempt (INFO level - normal operation)
    logger.info(
        f"Validation attempt - user_id: {current_user.id}, session_id: {session_id}"
    )
    
    # Retrieve session from database
    from app.models.session import Session as SessionModel
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        logger.warning(f"Session {session_id} not found for validation")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )
    
    # Verify session ownership (Requirement 1.4: restrict access)
    if session.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to validate session {session_id} "
            f"owned by user {session.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to validate this session"
        )
    
    # Verify session is active
    if session.status != "active":
        logger.warning(
            f"Cannot validate session {session_id} with status: {session.status}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is {session.status}, cannot validate"
        )
    
    try:
        # Get Docker client from session manager
        session_manager = get_session_manager()
        docker_client = session_manager.client
        
        # Get container from Docker
        container = docker_client.containers.get(session.container_id)
        logger.debug(f"Container {session.container_id} found for validation")
        
        # Execute validation script inside container (Requirement 6.1)
        logger.info(
            f"Executing validation script - session_id: {session_id}, "
            f"challenge_id: {session.challenge_id}"
        )
        result = container.exec_run(
            cmd="/bin/bash /challenge/validate.sh",
            user="1000:1000",
            workdir="/challenge"
        )
        
        exit_code = result.exit_code
        output = result.output.decode('utf-8', errors='replace').strip()
        
        logger.debug(
            f"Validation script completed for session {session_id}. "
            f"Exit code: {exit_code}"
        )
        
        # Import Attempt model for recording validation results
        from app.models.attempt import Attempt
        from datetime import datetime
        
        if exit_code == 0:
            # Success case (Requirement 6.2)
            # Calculate completion time (Requirement 6.5)
            completion_time = int((datetime.utcnow() - session.created_at).total_seconds())
            
            # Record successful attempt in database (Requirement 6.6)
            attempt = Attempt(
                user_id=current_user.id,
                challenge_id=session.challenge_id,
                session_id=session_id,
                success=True,
                completion_time_seconds=completion_time
            )
            db.add(attempt)
            
            # Update session status to completed
            session.status = "completed"
            session.terminated_at = datetime.utcnow()
            
            db.commit()
            
            # Log successful validation (INFO level - normal operation)
            logger.info(
                f"Validation successful - user_id: {current_user.id}, "
                f"session_id: {session_id}, challenge_id: {session.challenge_id}, "
                f"completion_time: {completion_time}s, result: success"
            )
            
            # Return success response
            return ValidationResponse(
                success=True,
                message=output if output else "Challenge completed successfully!",
                hint=None
            )
        else:
            # Failure case (Requirement 6.3)
            
            # Record failed attempt in database
            attempt = Attempt(
                user_id=current_user.id,
                challenge_id=session.challenge_id,
                session_id=session_id,
                success=False,
                completion_time_seconds=None
            )
            db.add(attempt)
            db.commit()
            
            # Parse output for hint message (Requirement 6.4)
            # The validation script should output a hint on failure
            hint = None
            message_lines = []
            
            for line in output.split('\n'):
                line = line.strip()
                if line:
                    if line.lower().startswith('hint:'):
                        # Extract hint
                        hint = line[5:].strip()
                    elif not line.startswith('✗') and not line.startswith('✓'):
                        # Collect message lines (excluding status symbols)
                        message_lines.append(line)
            
            # If no explicit hint found, use the full output as hint
            if not hint and output:
                hint = output
            
            # Build user-friendly message
            message = "Validation failed. The challenge is not yet solved."
            if message_lines:
                message = ' '.join(message_lines)
            
            # Log failed validation (INFO level - normal operation)
            logger.info(
                f"Validation failed - user_id: {current_user.id}, "
                f"session_id: {session_id}, challenge_id: {session.challenge_id}, "
                f"result: failed"
            )
            
            # Return failure response with hint (Requirement 6.4)
            return ValidationResponse(
                success=False,
                message=message,
                hint=hint
            )
        
    except docker.errors.NotFound:
        logger.error(f"Container {session.container_id} not found for session {session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Container not found. Session may have been terminated."
        )
    except docker.errors.APIError as e:
        logger.error(f"Docker API error during validation for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute validation: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during validation for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )

@router.websocket("/{session_id}/terminal")
async def terminal_websocket(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for terminal communication with Docker container.
    
    Establishes a bidirectional relay between the browser terminal (via WebSocket)
    and the Docker container's bash shell (via Docker exec).
    
    Requirements:
    - 4.1: Display terminal interface connected via WebSocket
    - 4.3: Execute commands and return output within 200ms
    - 13.2: Support WebSocket connections for terminal communication
    - 1.4: Restrict access to authenticated users
    
    Connection Flow:
    1. Accept WebSocket connection from browser
    2. Validate authentication token from query parameter
    3. Validate session exists, is active, and belongs to authenticated user
    4. Create Docker exec instance with /bin/bash
    5. Relay data bidirectionally:
       - Browser → WebSocket → Docker exec stdin
       - Docker exec stdout → WebSocket → Browser
    6. Clean up on disconnect
    
    Args:
        websocket: WebSocket connection from browser
        session_id: Session identifier for the container
        db: Database session
        
    Raises:
        WebSocket close with code 4001: Authentication failed
        WebSocket close with code 4003: Forbidden - user doesn't own session
        WebSocket close with code 4004: Session not found
        WebSocket close with code 4003: Session not active
        WebSocket close with code 5000: Internal error
    """
    # Accept WebSocket connection (Requirement 4.1)
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for session {session_id}")
    
    # Authenticate user via query parameter token (Requirement 1.4)
    # WebSocket doesn't support Authorization header in browser, so we use query param
    token = websocket.query_params.get("token")
    if not token:
        logger.warning(f"No authentication token provided for WebSocket connection to session {session_id}")
        await websocket.send_text("Error: Authentication required")
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    # Validate token and get user
    from app.services.auth_service import decode_access_token, get_user_by_id
    payload = decode_access_token(token)
    if payload is None:
        logger.warning(f"Invalid authentication token for WebSocket connection to session {session_id}")
        await websocket.send_text("Error: Invalid authentication token")
        await websocket.close(code=4001, reason="Invalid authentication token")
        return
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        logger.warning(f"No user ID in token for WebSocket connection to session {session_id}")
        await websocket.send_text("Error: Invalid authentication token")
        await websocket.close(code=4001, reason="Invalid authentication token")
        return
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        logger.warning(f"Invalid user ID format in token for WebSocket connection to session {session_id}")
        await websocket.send_text("Error: Invalid authentication token")
        await websocket.close(code=4001, reason="Invalid authentication token")
        return
    
    user = get_user_by_id(db, user_id)
    if user is None:
        logger.warning(f"User {user_id} not found for WebSocket connection to session {session_id}")
        await websocket.send_text("Error: User not found")
        await websocket.close(code=4001, reason="User not found")
        return
    
    logger.info(f"User {user.id} authenticated for WebSocket connection to session {session_id}")
    
    # Import asyncio for concurrent tasks
    import asyncio
    from docker.types import LogConfig
    
    # Retrieve session from database (Requirement 4.1)
    from app.models.session import Session as SessionModel
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        logger.warning(f"Session {session_id} not found for WebSocket connection")
        await websocket.send_text("Error: Session not found")
        await websocket.close(code=4004, reason="Session not found")
        return
    
    # Validate session ownership (Requirement 1.4)
    if session.user_id != user.id:
        logger.warning(
            f"User {user.id} attempted WebSocket connection to session {session_id} "
            f"owned by user {session.user_id}"
        )
        await websocket.send_text("Error: Access denied")
        await websocket.close(code=4003, reason="Access denied")
        return
    
    # Validate session is active
    if session.status != "active":
        logger.warning(
            f"Session {session_id} is not active (status: {session.status}) "
            f"for WebSocket connection"
        )
        await websocket.send_text(f"Error: Session is {session.status}")
        await websocket.close(code=4003, reason=f"Session is {session.status}")
        return
    
    # Get Docker client from session manager
    session_manager = get_session_manager()
    docker_client = session_manager.client
    
    try:
        # Get container from Docker (Requirement 13.2)
        container = docker_client.containers.get(session.container_id)
        logger.info(f"Container {session.container_id} found for session {session_id}")
        
        # Create exec instance with /bin/bash (Requirement 4.3)
        # This creates an interactive bash shell in the container
        exec_instance = docker_client.api.exec_create(
            container=container.id,
            cmd="/bin/bash",
            stdin=True,
            stdout=True,
            stderr=True,
            tty=True,
            user="1000:1000"  # Run as non-root user (same as container)
        )
        exec_id = exec_instance['Id']
        logger.info(f"Exec instance {exec_id} created for session {session_id}")
        
        # Start exec instance and get socket for bidirectional communication
        exec_socket = docker_client.api.exec_start(
            exec_id=exec_id,
            detach=False,
            tty=True,
            socket=True
        )
        logger.info(f"Exec instance {exec_id} started with socket connection")
        
        # Create tasks for bidirectional relay (Requirement 4.3)
        async def relay_websocket_to_exec():
            """
            Relay data from WebSocket (browser) to Docker exec (container stdin).
            
            This task receives user input from the browser terminal and writes it
            to the container's bash shell stdin.
            """
            try:
                while True:
                    # Receive data from WebSocket (browser terminal input)
                    data = await websocket.receive_text()
                    
                    # Write to Docker exec stdin (container shell)
                    exec_socket._sock.send(data.encode('utf-8'))
                    
            except Exception as e:
                logger.debug(f"WebSocket to exec relay ended for session {session_id}: {e}")
        
        async def relay_exec_to_websocket():
            """
            Relay data from Docker exec (container stdout) to WebSocket (browser).
            
            This task receives output from the container's bash shell and sends it
            to the browser terminal for display.
            """
            try:
                while True:
                    # Read from Docker exec socket (container shell output)
                    # Use select with timeout to avoid blocking indefinitely
                    import select
                    
                    # Wait for data with timeout
                    ready = select.select([exec_socket._sock], [], [], 0.1)
                    
                    if ready[0]:
                        # Data available, read it
                        data = exec_socket._sock.recv(4096)
                        
                        if not data:
                            # Socket closed
                            logger.info(f"Exec socket closed for session {session_id}")
                            break
                        
                        # Send to WebSocket (browser terminal)
                        await websocket.send_text(data.decode('utf-8', errors='replace'))
                    
                    # Small sleep to prevent busy loop
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.debug(f"Exec to WebSocket relay ended for session {session_id}: {e}")
        
        # Run both relay tasks concurrently (Requirement 4.3)
        relay_tasks = [
            asyncio.create_task(relay_websocket_to_exec()),
            asyncio.create_task(relay_exec_to_websocket())
        ]
        
        # Wait for either task to complete (happens on disconnect or error)
        done, pending = await asyncio.wait(
            relay_tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Terminal relay ended for session {session_id}")
        
    except docker.errors.NotFound:
        logger.error(f"Container {session.container_id} not found for session {session_id}")
        await websocket.send_text("Error: Container not found")
        await websocket.close(code=4004, reason="Container not found")
        return
        
    except Exception as e:
        logger.error(f"Error in terminal WebSocket for session {session_id}: {e}")
        try:
            await websocket.send_text(f"Error: {str(e)}")
            await websocket.close(code=5000, reason="Internal error")
        except:
            pass
        return
    
    finally:
        # Cleanup: close exec socket and WebSocket (Requirement 4.3)
        try:
            exec_socket.close()
            logger.info(f"Exec socket closed for session {session_id}")
        except:
            pass
        
        try:
            await websocket.close()
            logger.info(f"WebSocket closed for session {session_id}")
        except:
            pass
