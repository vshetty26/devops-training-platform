# Implementation Plan: DevOps Arena

## Overview

This implementation plan prioritizes delivering a working end-to-end flow early: users can authenticate, start one challenge, interact via browser terminal, and validate their solution. After this MVP is functional, we expand to include additional challenges, leaderboards, and finally deployment infrastructure.

The implementation uses:
- **Frontend**: React + Vite + Tailwind CSS + xterm.js
- **Backend**: Python + FastAPI + Docker SDK
- **Database**: SQLite with SQLAlchemy ORM
- **Container Runtime**: Docker

## Tasks

- [x] 1. Set up project structure and core infrastructure
  - Create frontend directory with Vite + React + Tailwind CSS scaffolding
  - Create backend directory with FastAPI + Python project structure
  - Set up SQLite database with SQLAlchemy models for users, challenges, sessions, attempts
  - Create Docker Compose configuration for local development
  - Initialize Git repository with .gitignore files
  - _Requirements: 20.1, 20.2, 20.3, 20.5, 12.1, 12.2, 13.1_

- [x] 2. Implement backend authentication system
  - [x] 2.1 Create user authentication API endpoints
    - Implement POST /api/auth/login endpoint with password hashing (bcrypt)
    - Implement JWT token generation and validation middleware
    - Create user registration endpoint (POST /api/auth/register)
    - Add database operations for user creation and retrieval
    - _Requirements: 1.1, 1.2, 1.5_
  
  - [x]* 2.2 Write unit tests for authentication
    - Test password hashing and verification
    - Test JWT token generation and validation
    - Test authentication middleware with valid/invalid tokens
    - Test login endpoint with valid and invalid credentials
    - _Requirements: 1.1, 1.2_

- [x] 3. Implement frontend authentication UI
  - [x] 3.1 Create login page and authentication context
    - Build login form component with username/password fields
    - Implement React Context for global authentication state
    - Add form validation and error message display
    - Store JWT token in localStorage and handle session persistence
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x]* 3.2 Write unit tests for authentication components
    - Test login form submission and validation
    - Test authentication context state management
    - Test token storage and retrieval
    - _Requirements: 1.1, 1.4_

- [x] 4. Create single challenge definition (Nginx 502)
  - [x] 4.1 Build challenge directory structure
    - Create /challenges/nginx-502/ directory
    - Write Dockerfile with Ubuntu base, Nginx, and non-root user
    - Write setup.sh script to inject broken upstream configuration
    - Write validate.sh script to check for HTTP 200 response
    - Create metadata.json with title, difficulty, brief, and hints
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.3_
  
  - [x]* 4.2 Test challenge definition locally
    - Build Docker image and verify container starts
    - Run setup.sh and verify fault is injected
    - Manually fix the issue and verify validate.sh returns exit 0
    - _Requirements: 7.3, 7.4_

- [x] 5. Implement backend session management
  - [x] 5.1 Create session manager module
    - Implement create_session function using Docker SDK for Python
    - Configure container security constraints (non-root user, capabilities, resource limits, network isolation)
    - Execute challenge setup.sh script after container creation
    - Store session metadata in database and in-memory tracker
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 11.1, 11.2, 11.3, 11.4, 14.1, 14.2_
  
  - [x] 5.2 Implement session termination and timeout enforcement
    - Create terminate_session function to stop and remove containers
    - Implement 30-minute timeout using asyncio tasks
    - Add cleanup logic to prevent resource leaks
    - _Requirements: 5.1, 5.2, 5.3, 14.3, 14.4, 14.5_
  
  - [x]* 5.3 Write unit tests for session manager
    - Test session creation with mocked Docker client
    - Test timeout enforcement logic
    - Test session termination and cleanup
    - Test resource limit configuration
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 6. Implement backend API endpoints for challenges and sessions
  - [x] 6.1 Create challenge API endpoints
    - Implement GET /api/challenges endpoint to list all challenges
    - Implement GET /api/challenges/{id} endpoint for challenge details
    - Load challenge metadata from filesystem on backend startup
    - _Requirements: 2.1, 2.2, 2.3, 7.6_
  
  - [x] 6.2 Create session API endpoints
    - Implement POST /api/sessions endpoint to create new session
    - Implement DELETE /api/sessions/{id} endpoint to terminate session
    - Add request/response validation with Pydantic models
    - _Requirements: 3.1, 5.1, 13.5_
  
  - [x]* 6.3 Write integration tests for API endpoints
    - Test challenge listing and detail retrieval
    - Test session creation with real Docker containers
    - Test session termination
    - _Requirements: 2.1, 3.1_

- [x] 7. Checkpoint - Backend session management working
  - Verify container creation, timeout, and termination work correctly
  - Test with Docker running locally
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement WebSocket terminal handler
  - [x] 8.1 Create WebSocket endpoint for terminal communication
    - Implement WebSocket endpoint at /api/sessions/{session_id}/terminal
    - Validate session ownership and existence
    - Use Docker SDK to create exec instance with /bin/bash in container
    - Implement bidirectional relay between WebSocket and Docker exec stdin/stdout
    - Handle WebSocket disconnect and exec process cleanup
    - _Requirements: 4.1, 4.3, 13.2_
  
  - [x]* 8.2 Test WebSocket terminal functionality
    - Test WebSocket connection establishment
    - Test command execution and output relay
    - Test connection cleanup on disconnect
    - _Requirements: 4.3, 4.4_

- [x] 9. Implement frontend terminal component
  - [x] 9.1 Create browser terminal with xterm.js
    - Install xterm.js and xterm-addon-fit packages
    - Create TerminalComponent with xterm.js instance
    - Configure terminal appearance (font, colors, cursor)
    - Implement WebSocket connection management
    - Wire terminal input to WebSocket send, WebSocket messages to terminal write
    - Add connection status indicator and error handling
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 12.3_
  
  - [x]* 9.2 Write unit tests for terminal component
    - Test WebSocket connection establishment
    - Test terminal data relay
    - Test cleanup on unmount
    - _Requirements: 4.2, 4.3_

- [x] 10. Implement frontend challenge UI
  - [x] 10.1 Create challenge list page
    - Build ChallengeListComponent to fetch and display challenges
    - Display challenge title, difficulty, and brief description
    - Add navigation to challenge detail on click
    - Style with Tailwind CSS for responsive layout
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 12.2_
  
  - [x] 10.2 Create challenge detail page
    - Build ChallengeDetailComponent with challenge brief display
    - Add "Start Challenge" button to create session via API
    - Display session timeout countdown timer
    - Integrate TerminalComponent for active sessions
    - Add "Check Solution" button and display validation results
    - Add "End Session" button for manual termination
    - _Requirements: 2.4, 3.1, 4.1, 5.5, 6.1_
  
  - [x]* 10.3 Write integration tests for challenge UI
    - Test challenge list rendering
    - Test challenge detail rendering
    - Test session creation flow
    - _Requirements: 2.1, 2.4_

- [x] 11. Implement backend validation service
  - [x] 11.1 Create validation endpoint and service
    - Implement POST /api/sessions/{session_id}/validate endpoint
    - Execute validate.sh script inside container using Docker exec
    - Parse exit code and stdout for success/failure and hints
    - Record successful attempts in database with completion time
    - Return validation response with success flag, message, and optional hint
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [x]* 11.2 Write unit tests for validation service
    - Test validation script execution
    - Test exit code parsing
    - Test attempt recording in database
    - Test hint extraction from stdout
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 12. Checkpoint - End-to-end MVP flow working
  - Test complete flow: login → browse challenge → start session → connect terminal → debug → validate
  - Verify timeout enforcement after 30 minutes
  - Verify container cleanup after session end
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Add remaining challenge definitions
  - [x] 13.1 Create Docker restart loop challenge
    - Write Dockerfile, setup.sh, validate.sh, metadata.json
    - Inject container restart loop fault in setup script
    - Validate that container runs stably without restart
    - _Requirements: 8.1, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 13.2 Create disk full challenge
    - Write Dockerfile, setup.sh, validate.sh, metadata.json
    - Fill disk with dummy data in setup script
    - Validate that sufficient disk space is available
    - _Requirements: 8.2, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 13.3 Create GitHub Actions workflow YAML challenge
    - Write Dockerfile, setup.sh, validate.sh, metadata.json
    - Inject syntax error in workflow YAML in setup script
    - Validate that YAML is syntactically correct
    - _Requirements: 8.4, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 13.4 Create Kubernetes CrashLoopBackOff challenge
    - Write Dockerfile, setup.sh, validate.sh, metadata.json
    - Inject misconfigured pod manifest in setup script
    - Validate that pod starts successfully
    - _Requirements: 8.5, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x]* 13.5 Test all challenge definitions
    - Build all challenge Docker images
    - Test each setup and validation script
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 14. Implement leaderboard functionality
  - [x] 14.1 Create backend leaderboard API endpoints
    - Implement GET /api/leaderboard/global endpoint
    - Implement GET /api/leaderboard/challenges/{id} endpoint
    - Query and rank users by completion count and time
    - Add database indexes for efficient leaderboard queries
    - _Requirements: 9.1, 9.2, 9.3, 9.5_
  
  - [x] 14.2 Create frontend leaderboard page
    - Build LeaderboardComponent to fetch and display rankings
    - Show username, completion time, and rank
    - Add filter toggle for global vs per-challenge view
    - Update leaderboard data after validation success
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x]* 14.3 Write tests for leaderboard
    - Test leaderboard ranking logic
    - Test leaderboard API endpoints
    - Test leaderboard component rendering
    - _Requirements: 9.1, 9.2, 9.4_

- [x] 15. Implement challenge completion status tracking
  - [x] 15.1 Add completion status to challenge list
    - Query user's completed challenges from database
    - Display completion indicator on challenge list
    - Show completion time on completed challenges
    - _Requirements: 2.5, 1.3_
  
  - [x]* 15.2 Test completion status display
    - Test completion status query logic
    - Test UI rendering with completed and incomplete challenges
    - _Requirements: 2.5_

- [x] 16. Add security enhancements and logging
  - [x] 16.1 Implement comprehensive security checks
    - Verify Docker socket is not accessible from containers
    - Verify host filesystem is not mounted in containers
    - Add attempt logging for prohibited operations
    - _Requirements: 11.2, 11.3, 11.5_
  
  - [x] 16.2 Add structured logging
    - Configure logging with levels (DEBUG, INFO, WARNING, ERROR)
    - Log container lifecycle events (create, start, stop, remove)
    - Log authentication events (login, failed attempts)
    - Log validation attempts and results
    - Ensure no sensitive data is logged
    - _Requirements: 11.5_
  
  - [x]* 16.3 Perform security testing
    - Test container escape attempts
    - Test host filesystem access attempts
    - Test network isolation
    - Test unauthorized session access
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 17. Checkpoint - Full platform functionality complete
  - Test all 5 challenges work correctly
  - Test leaderboard updates accurately
  - Test security constraints are enforced
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Create Docker Compose deployment configuration
  - [x] 18.1 Write production Docker Compose file
    - Define frontend service with Nginx serving static build
    - Define backend service with FastAPI
    - Configure SQLite database persistence with Docker volumes
    - Set up frontend-backend networking
    - Configure environment variables for production
    - _Requirements: 15.1, 15.3, 15.4, 15.5_
  
  - [x]* 18.2 Test Docker Compose deployment locally
    - Build production images
    - Test deployment with docker-compose up
    - Verify frontend-backend communication
    - Verify database persistence across restarts
    - _Requirements: 15.1, 15.4, 15.5_

- [x] 19. Set up CI/CD pipeline with GitHub Actions
  - [x] 19.1 Create GitHub Actions workflow
    - Write workflow YAML for continuous integration
    - Add linting checks for frontend (ESLint) and backend (Flake8/Black)
    - Add unit test execution with coverage reporting
    - Add Docker image build step
    - _Requirements: 16.1, 16.2, 16.3, 16.4_
  
  - [x] 19.2 Add deployment automation
    - Add deployment step triggered on main branch
    - Configure SSH connection to EC2 instance
    - Add docker-compose pull and restart commands
    - _Requirements: 16.5, 15.2_
  
  - [x]* 19.3 Test CI/CD pipeline
    - Trigger workflow on pull request
    - Verify all checks pass
    - Test deployment to staging environment
    - _Requirements: 16.5_

- [x] 20. Create project documentation
  - [x] 20.1 Write comprehensive README.md
    - Add project overview and features list
    - Include architecture diagram using Mermaid syntax
    - Write local development setup instructions
    - Write production deployment instructions for AWS EC2
    - Add placeholder for demo GIF
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_
  
  - [x] 20.2 Add inline code documentation
    - Add docstrings to all Python functions and classes
    - Add JSDoc comments to key React components
    - Document API endpoints with OpenAPI/Swagger
    - _Requirements: 13.3, 12.4_
  
  - [x]* 20.3 Create developer contribution guide
    - Document how to add new challenges
    - Document code style guidelines
    - Document testing requirements
    - _Requirements: 19.1, 20.4_

- [x] 21. Final validation and deployment
  - [x] 21.1 Deploy to AWS EC2 free-tier instance
    - Provision EC2 instance with Docker installed
    - Configure security groups for HTTP access
    - Deploy using Docker Compose
    - Verify platform is accessible via public IP
    - _Requirements: 15.2, 15.3_
  
  - [x]* 21.2 Perform end-to-end testing on production
    - Test all challenges on deployed instance
    - Test multiple concurrent users
    - Test session timeout enforcement
    - Monitor resource usage
    - _Requirements: 3.4, 5.1, 11.4_

- [x] 22. Final checkpoint - Platform ready for users
  - Ensure all features are working in production
  - Verify documentation is complete
  - Verify CI/CD pipeline deploys successfully
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- The task order prioritizes getting a working end-to-end flow (tasks 1-12) before expanding features
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Security constraints are implemented early (task 5) and validated later (task 16)
- Database schema is created upfront (task 1) to support all subsequent features
- Challenge definitions are modular and can be added incrementally
- The Docker Compose configuration assumes Docker is pre-installed on the deployment target

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "4.1"] },
    { "id": 2, "tasks": ["2.2", "3.1", "4.2", "5.1"] },
    { "id": 3, "tasks": ["3.2", "5.2", "6.1"] },
    { "id": 4, "tasks": ["5.3", "6.2", "8.1"] },
    { "id": 5, "tasks": ["6.3", "8.2", "9.1"] },
    { "id": 6, "tasks": ["9.2", "10.1"] },
    { "id": 7, "tasks": ["10.2", "11.1"] },
    { "id": 8, "tasks": ["10.3", "11.2"] },
    { "id": 9, "tasks": ["13.1", "13.2", "13.3", "13.4"] },
    { "id": 10, "tasks": ["13.5", "14.1"] },
    { "id": 11, "tasks": ["14.2", "15.1"] },
    { "id": 12, "tasks": ["14.3", "15.2", "16.1"] },
    { "id": 13, "tasks": ["16.2"] },
    { "id": 14, "tasks": ["16.3", "18.1"] },
    { "id": 15, "tasks": ["18.2", "19.1"] },
    { "id": 16, "tasks": ["19.2", "20.1"] },
    { "id": 17, "tasks": ["19.3", "20.2"] },
    { "id": 18, "tasks": ["20.3", "21.1"] },
    { "id": 19, "tasks": ["21.2"] }
  ]
}
```
