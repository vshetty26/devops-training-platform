# Authentication Flow Diagrams

## User Registration Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as POST /api/auth/register
    participant AuthService as auth_service.py
    participant Database
    
    Client->>API: {username, password}
    API->>AuthService: create_user(username, password)
    AuthService->>AuthService: get_password_hash(password)
    Note over AuthService: Bcrypt hashing with salt
    AuthService->>Database: INSERT User (username, password_hash)
    Database-->>AuthService: User object
    AuthService-->>API: User object
    API-->>Client: {id, username, created_at} [201]
    
    Note over Client,Database: Requirements: 1.5 (secure password storage)
```

## User Login Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as POST /api/auth/login
    participant AuthService as auth_service.py
    participant Database
    
    Client->>API: {username, password}
    API->>AuthService: authenticate_user(username, password)
    AuthService->>Database: SELECT User WHERE username
    Database-->>AuthService: User object (with password_hash)
    AuthService->>AuthService: verify_password(password, password_hash)
    Note over AuthService: Bcrypt verification
    
    alt Valid Credentials
        AuthService-->>API: User object
        API->>AuthService: create_access_token({sub: user_id})
        Note over AuthService: JWT with 30min expiry
        AuthService-->>API: JWT token
        API-->>Client: {token, user} [200]
    else Invalid Credentials
        AuthService-->>API: None
        API-->>Client: {detail: "Invalid credentials"} [401]
        Note over Client,Database: Requirements: 1.1, 1.2 (< 500ms)
    end
```

## Protected Endpoint Access Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as GET /api/auth/me
    participant Dependency as get_current_user()
    participant AuthService as auth_service.py
    participant Database
    
    Client->>API: Authorization: Bearer <token>
    API->>Dependency: HTTPBearer extracts token
    Dependency->>AuthService: decode_access_token(token)
    
    alt Valid Token
        AuthService-->>Dependency: {sub: user_id, exp: timestamp}
        Dependency->>Database: SELECT User WHERE id = user_id
        Database-->>Dependency: User object
        Dependency-->>API: User object
        API-->>Client: {id, username, created_at} [200]
    else Invalid/Expired Token
        AuthService-->>Dependency: None
        Dependency-->>Client: {detail: "Could not validate credentials"} [401]
    end
    
    Note over Client,Database: Requirements: 1.1, 1.3 (user association)
```

## Complete Authentication System

```mermaid
graph TB
    subgraph "Client Layer"
        Client[Frontend Client]
    end
    
    subgraph "API Layer"
        Register[POST /register]
        Login[POST /login]
        Me[GET /me]
    end
    
    subgraph "Service Layer"
        AuthService[auth_service.py]
        Bcrypt[Bcrypt Password Hashing]
        JWT[JWT Token Operations]
    end
    
    subgraph "Middleware Layer"
        Dependency[get_current_user Dependency]
    end
    
    subgraph "Data Layer"
        DB[(SQLite Database)]
        UserModel[User Model]
    end
    
    Client -->|username, password| Register
    Client -->|username, password| Login
    Client -->|Bearer token| Me
    
    Register --> AuthService
    Login --> AuthService
    Me --> Dependency
    
    Dependency --> JWT
    Dependency --> DB
    
    AuthService --> Bcrypt
    AuthService --> JWT
    AuthService --> DB
    
    DB --> UserModel
    
    style Bcrypt fill:#90EE90
    style JWT fill:#87CEEB
    style DB fill:#FFD700
    
    classDef security fill:#90EE90,stroke:#333,stroke-width:2px
    class Bcrypt,JWT security
```

## Security Components

### Password Hashing (Bcrypt)
```
Plain Password -> Bcrypt Hash (with automatic salt) -> Stored Hash
     |                      |                              |
 "password123"    Random salt generated          "$2b$12$..."
                  Cost factor: 12
                  Unique per password
```

### JWT Token Structure
```
Header.Payload.Signature

Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "sub": "123",              # User ID
  "exp": 1234567890          # Expiration timestamp
}

Signature:
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  SECRET_KEY
)
```

### Token Validation Process
```
1. Extract token from Authorization header
2. Decode JWT and verify signature
3. Check expiration timestamp
4. Extract user ID from "sub" claim
5. Query database for user
6. Return User object to endpoint
```

## Error Handling

### Registration Errors
- **400 Bad Request**: Username already exists
- **422 Unprocessable Entity**: Invalid request data (missing fields, wrong types)

### Login Errors
- **401 Unauthorized**: Invalid username or password (same message for both to prevent enumeration)
- **422 Unprocessable Entity**: Invalid request data

### Protected Endpoint Errors
- **401 Unauthorized**: Invalid, expired, or malformed token
- **403 Forbidden**: No Authorization header provided

## Performance Requirements

### Requirement 1.2: Response Time
Login endpoint must return errors within **500ms**:
- Database query: ~1-5ms (SQLite in-memory)
- Password verification: ~50-100ms (bcrypt cost factor 12)
- JWT generation: ~1-2ms
- Total: < 200ms (well within requirement)

## Requirements Mapping

| Requirement | Implementation | Location |
|-------------|----------------|----------|
| 1.1 | Authenticated session creation | `POST /login`, `create_access_token()` |
| 1.2 | Invalid credentials error < 500ms | `POST /login` returns 401 |
| 1.3 | User association | JWT "sub" claim, `get_current_user()` |
| 1.4 | Restrict unauthenticated access | `get_current_user()` dependency |
| 1.5 | Secure password storage | `get_password_hash()`, bcrypt |
