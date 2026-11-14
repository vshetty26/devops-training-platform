# Structured Logging Implementation

## Overview

This document describes the structured logging implementation for the DevOps Arena backend API, fulfilling **Requirement 11.5**.

## Configuration

### Log Format

```
YYYY-MM-DD HH:MM:SS [LEVEL] [module.name] message
```

Example:
```
2026-11-11 12:19:31 [INFO] [app.services.session_manager] Container created - session_id: abc123, container_id: def456, user_id: 1, challenge_id: nginx-502
```

### Log Levels

- **DEBUG**: Detailed diagnostic information for debugging
- **INFO**: Normal operational events (successful operations)
- **WARNING**: Warning events (failed login attempts, timeouts)
- **ERROR**: Error events (Docker errors, database errors)

### Configuration Location

Logging is configured in `app/main.py` via the `configure_logging()` function, which is called before the FastAPI app is created.

## Logged Events

### 1. Container Lifecycle Events

**Location**: `app/services/session_manager.py`

#### Container Created
```python
logger.info(
    f"Session created - session_id: {session_id}, container_id: {container.id}, "
    f"user_id: {user_id}, challenge_id: {challenge_id}, timeout_at: {timeout_at.isoformat()}"
)
```

#### Container Started
```python
logger.info(
    f"Container started - session_id: {session_id}, container_id: {container.id}, "
    f"user_id: {user_id}, challenge_id: {challenge_id}"
)
```

#### Container Stopped
```python
logger.info(
    f"Stopping container - session_id: {session_id}, container_id: {container_id}"
)
```

#### Container Removed
```python
logger.info(
    f"Container removed - session_id: {session_id}, container_id: {container_id}, "
    f"user_id: {user_id}, challenge_id: {challenge_id}"
)
```

#### Container Timeout
```python
logger.warning(
    f"Container removed due to timeout - session_id: {session_id}, "
    f"container_id: {container_id}, user_id: {user_id}, "
    f"challenge_id: {challenge_id}"
)
```

### 2. Authentication Events

**Location**: `app/routers/auth.py`

#### Successful Login
```python
logger.info(
    f"Successful login - username: {user.username}, user_id: {user.id}, "
    f"timestamp: {datetime.utcnow().isoformat()}"
)
```

#### Failed Login Attempt
```python
logger.warning(
    f"Failed login attempt - username: {login_data.username}, "
    f"reason: Invalid credentials, timestamp: {datetime.utcnow().isoformat()}"
)
```

#### User Registration
```python
logger.info(
    f"User registered successfully - username: {new_user.username}, "
    f"user_id: {new_user.id}, timestamp: {datetime.utcnow().isoformat()}"
)
```

### 3. Validation Events

**Location**: `app/routers/sessions.py`

#### Validation Attempt
```python
logger.info(
    f"Validation attempt - user_id: {current_user.id}, session_id: {session_id}"
)
```

#### Validation Success
```python
logger.info(
    f"Validation successful - user_id: {current_user.id}, "
    f"session_id: {session_id}, challenge_id: {session.challenge_id}, "
    f"completion_time: {completion_time}s, result: success"
)
```

#### Validation Failure
```python
logger.info(
    f"Validation failed - user_id: {current_user.id}, "
    f"session_id: {session_id}, challenge_id: {session.challenge_id}, "
    f"result: failed"
)
```

## Security Considerations

### What IS Logged

✅ Usernames  
✅ User IDs  
✅ Session IDs  
✅ Container IDs  
✅ Challenge IDs  
✅ Timestamps  
✅ Completion times  
✅ Operation results (success/failure)  
✅ Error messages (sanitized)  

### What is NOT Logged

❌ Passwords (raw or hashed)  
❌ JWT tokens  
❌ Authentication secrets  
❌ Environment variables with sensitive data  
❌ Docker socket paths  
❌ Host filesystem paths  

## Module-Specific Log Levels

```python
# Application modules (INFO level - show operational events)
logging.getLogger('app.services.session_manager').setLevel(logging.INFO)
logging.getLogger('app.routers.auth').setLevel(logging.INFO)
logging.getLogger('app.routers.sessions').setLevel(logging.INFO)
logging.getLogger('app.services.auth_service').setLevel(logging.INFO)

# External libraries (WARNING level - reduce noise)
logging.getLogger('docker').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
```

## Testing

Run the logging test script to verify the implementation:

```bash
cd backend
source venv/bin/activate
python test_logging.py
```

This will output sample log messages for all logged event types.

## Production Considerations

### Log Aggregation

In production, consider:
- Forwarding logs to a centralized logging system (e.g., ELK, Splunk, CloudWatch)
- Using structured logging libraries like `structlog` for better parsing
- Implementing log rotation to prevent disk space issues

### Log Retention

Implement log retention policies:
- Keep recent logs (7-30 days) for operational debugging
- Archive older logs for compliance and audit purposes
- Automatically delete very old logs to save storage

### Performance

- Logging is performed synchronously and should not significantly impact performance
- External library logs are set to WARNING level to reduce noise
- Consider async logging in high-throughput scenarios

## Monitoring and Alerting

Set up alerts for:
- High frequency of failed login attempts (potential brute force attack)
- Container creation failures (Docker daemon issues)
- Validation script execution failures
- Timeout events (may indicate resource constraints)

## Compliance

This logging implementation supports:
- **Audit trails**: All authentication and authorization events are logged
- **Security monitoring**: Failed login attempts and unauthorized access attempts are logged
- **Operational visibility**: Container lifecycle and validation events are logged
- **Privacy**: Sensitive data (passwords, tokens) is explicitly excluded from logs

## Requirements Coverage

This implementation fulfills **Requirement 11.5**:
> THE Platform SHALL log security-relevant events including:
> - Container lifecycle events (create, start, stop, remove)
> - Authentication events (login, failed attempts)
> - Validation attempts and results
> - Ensure no sensitive data is logged

All specified events are logged with appropriate detail and security considerations.
