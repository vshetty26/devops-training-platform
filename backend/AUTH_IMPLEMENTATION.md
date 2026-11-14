# Authentication Implementation

This document describes the user authentication system implemented for DevOps Arena.

## Overview

The authentication system provides secure user registration, login, and session management using JWT (JSON Web Tokens) and bcrypt password hashing.

## Requirements Coverage

### Requirement 1.1: User Authentication
✓ Users can log in with valid credentials
✓ Authenticated sessions are created via JWT tokens
✓ JWT tokens are associated with user identifiers

### Requirement 1.2: Invalid Credentials Error
✓ Invalid credentials return HTTP 401 Unauthorized
✓ Authentication error messages are returned within 500ms
✓ Clear error messages provided for failed authentication

### Requirement 1.3: User Association
✓ All challenge attempts are associated with authenticated user ID
✓ JWT tokens contain user ID in the "sub" claim
✓ Protected endpoints extract user information from tokens

### Requirement 1.5: Secure Password Storage
✓ Passwords are hashed using bcrypt
✓ Plain text passwords are never stored
✓ Each password generates a unique hash (salt included)

## Implementation Components

### 1. Authentication Service (`app/services/auth_service.py`)

Core authentication logic including:

- **Password Hashing**
  - `get_password_hash(password)`: Hash passwords with bcrypt
  - `verify_password(plain, hashed)`: Verify password against hash

- **JWT Token Operations**
  - `create_access_token(data, expires_delta)`: Generate JWT tokens
  - `decode_access_token(token)`: Validate and decode tokens
  - Default expiration: 30 minutes
  - Algorithm: HS256

- **User Management**
  - `create_user(db, username, password)`: Create new users with hashed passwords
  - `authenticate_user(db, username, password)`: Validate credentials
  - `get_user_by_id(db, user_id)`: Retrieve user by ID

### 2. Authentication Dependencies (`app/dependencies.py`)

FastAPI dependencies for protecting endpoints:

- **`get_current_user(credentials, db)`**
  - Dependency for protected endpoints
  - Extracts JWT from Authorization header
  - Validates token and returns authenticated User object
  - Raises 401 if token is invalid or expired

- **`get_current_user_optional(credentials, db)`**
  - Optional authentication dependency
  - Returns User object if authenticated, None otherwise
  - Does not raise exceptions for missing credentials

### 3. API Endpoints (`app/routers/auth.py`)

Three authentication endpoints:

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- 400: Username already exists
- 422: Invalid request data

#### POST /api/auth/login
Authenticate and receive JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "string",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- 401: Invalid credentials (returned within 500ms)
- 422: Invalid request data

#### GET /api/auth/me
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- 401: Invalid or expired token
- 403: No credentials provided

## Database Schema

### users Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | UNIQUE, NOT NULL |
| password_hash | TEXT | NOT NULL |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

## Usage Examples

### Protecting Endpoints

To protect an endpoint with authentication:

```python
from fastapi import Depends
from app.dependencies import get_current_user
from app.models.user import User

@router.get("/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_user)
):
    return {"message": f"Hello {current_user.username}"}
```

### Optional Authentication

For endpoints that work with or without authentication:

```python
from fastapi import Depends
from typing import Optional
from app.dependencies import get_current_user_optional
from app.models.user import User

@router.get("/public-or-private")
async def flexible_endpoint(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    if current_user:
        return {"message": f"Welcome back, {current_user.username}"}
    else:
        return {"message": "Welcome, guest"}
```

## Security Considerations

### Password Security
- Bcrypt algorithm with automatic salt generation
- Each password generates a unique hash
- Passwords are never stored in plain text
- Password verification is constant-time to prevent timing attacks

### Token Security
- JWT tokens signed with HS256 algorithm
- Tokens expire after 30 minutes
- Secret key should be stored in environment variables (TODO: production)
- Tokens include expiration timestamp ("exp" claim)

### API Security
- All password validation errors return the same message to prevent user enumeration
- Protected endpoints require valid JWT token in Authorization header
- Token validation happens before endpoint logic execution
- Database queries use SQLAlchemy ORM to prevent SQL injection

## Testing

### Unit Tests (`tests/test_auth_service.py`)

Tests for authentication service functions:
- Password hashing and verification
- JWT token creation and validation
- User authentication logic
- User creation and retrieval

### Integration Tests (`tests/test_auth_api.py`)

Tests for API endpoints:
- User registration flow
- Login with valid/invalid credentials
- Protected endpoint access with tokens
- Complete authentication flow

Run tests with:
```bash
pytest tests/test_auth_service.py -v
pytest tests/test_auth_api.py -v
```

## Configuration

### Environment Variables (Production)

The following environment variables should be set in production:

- `SECRET_KEY`: JWT signing key (currently hardcoded, must be changed)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)
- `ALGORITHM`: JWT algorithm (default: HS256)

Example `.env` file:
```
SECRET_KEY=your-very-secure-secret-key-min-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

## Future Enhancements

- [ ] Move SECRET_KEY to environment variables
- [ ] Add refresh token support for longer sessions
- [ ] Implement password strength validation
- [ ] Add rate limiting for login attempts
- [ ] Add email verification for registration
- [ ] Implement password reset functionality
- [ ] Add OAuth2 social login support
- [ ] Implement token revocation/blacklist
- [ ] Add multi-factor authentication (MFA)
- [ ] Add audit logging for authentication events
