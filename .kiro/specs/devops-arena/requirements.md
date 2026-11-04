# Requirements Document

## Introduction

DevOps Arena is a browser-based interactive learning platform that enables users to practice troubleshooting real-world DevOps incidents in isolated sandbox environments. The system presents users with broken infrastructure scenarios and validates their fixes, similar to LeetCode but focused on operational incident response. The platform targets DevOps engineers, SRE practitioners, and students building practical troubleshooting skills.

## Glossary

- **Platform**: The complete DevOps Arena web application system
- **Challenge**: A single broken infrastructure scenario with validation criteria
- **Session**: An isolated container instance provisioned for one user attempt at one challenge
- **User**: An authenticated person attempting challenges on the platform
- **Container**: A Docker-isolated sandbox environment where users debug challenges
- **Validator**: A challenge-specific script that verifies if the user has fixed the issue
- **Terminal**: The browser-based command-line interface connected to the container via WebSocket
- **Session_Manager**: The backend service responsible for container lifecycle operations
- **Leaderboard**: The ranked list of users sorted by challenge completion metrics
- **Frontend**: The React-based web application served to users
- **Backend**: The FastAPI Python service handling API and WebSocket connections
- **Challenge_Definition**: The collection of files defining one challenge scenario
- **Incident_Brief**: The problem description presented to users at challenge start

## Requirements

### Requirement 1: User Authentication

**User Story:** As a user, I want to log in with a username, so that my progress and completion times are tracked.

#### Acceptance Criteria

1. WHEN a user submits valid login credentials, THE Platform SHALL create an authenticated session
2. WHEN a user submits invalid credentials, THE Platform SHALL return an authentication error message within 500ms
3. THE Platform SHALL associate all challenge attempts with the authenticated user identifier
4. WHEN a user is not authenticated, THE Platform SHALL restrict access to challenge pages
5. THE Platform SHALL store user credentials securely using password hashing

### Requirement 2: Challenge List Display

**User Story:** As a user, I want to browse available challenges with difficulty indicators, so that I can select challenges matching my skill level.

#### Acceptance Criteria

1. THE Platform SHALL display all available challenges on the challenge list page
2. THE Platform SHALL display difficulty level tags for each challenge
3. THE Platform SHALL display a short incident description for each challenge
4. WHEN a user clicks a challenge, THE Platform SHALL navigate to the challenge detail page
5. THE Platform SHALL indicate challenge completion status for the authenticated user

### Requirement 3: Challenge Session Provisioning

**User Story:** As a user, I want a fresh isolated environment when I start a challenge, so that I debug a clean broken system.

#### Acceptance Criteria

1. WHEN a user starts a challenge, THE Session_Manager SHALL provision a new Docker container within 10 seconds
2. THE Session_Manager SHALL inject the challenge-specific fault into the container during provisioning
3. THE Session_Manager SHALL enforce a CPU limit of 0.5 cores per container
4. THE Session_Manager SHALL enforce a memory limit of 256MB per container
5. THE Session_Manager SHALL block all network egress from the container
6. THE Session_Manager SHALL configure the container to run processes as a non-root user
7. THE Session_Manager SHALL drop all unnecessary Linux capabilities from the container

### Requirement 4: Browser Terminal Interface

**User Story:** As a user, I want a working terminal in my browser, so that I can debug the broken environment without leaving the web page.

#### Acceptance Criteria

1. WHEN a challenge session starts, THE Frontend SHALL display a terminal interface using xterm.js
2. THE Terminal SHALL connect to the container via WebSocket within 2 seconds of session creation
3. WHEN a user types commands in the terminal, THE Platform SHALL execute them in the container and return output within 200ms for non-blocking commands
4. THE Terminal SHALL display real-time command output as it is generated
5. THE Terminal SHALL support standard terminal features including command history and cursor navigation

### Requirement 5: Session Time Limits

**User Story:** As a platform operator, I want sessions to automatically terminate after 30 minutes, so that I prevent resource exhaustion.

#### Acceptance Criteria

1. WHEN a session is created, THE Session_Manager SHALL start a 30-minute countdown timer
2. WHEN the countdown reaches zero, THE Session_Manager SHALL terminate the container
3. THE Session_Manager SHALL remove all container resources after termination
4. WHEN a session is terminated, THE Frontend SHALL display a timeout message to the user
5. THE Frontend SHALL display the remaining time to the user during the session

### Requirement 6: Solution Validation

**User Story:** As a user, I want to verify my fix is correct, so that I know if I solved the challenge successfully.

#### Acceptance Criteria

1. WHEN a user clicks the check button, THE Validator SHALL execute the challenge-specific validation script inside the container
2. WHEN the validation script exits with code 0, THE Platform SHALL mark the attempt as successful
3. WHEN the validation script exits with a non-zero code, THE Platform SHALL mark the attempt as failed
4. WHEN validation fails, THE Platform SHALL display a hint message to the user
5. THE Platform SHALL record the completion time from session start to successful validation
6. WHEN validation succeeds, THE Platform SHALL persist the successful attempt to the database

### Requirement 7: Challenge Definition Structure

**User Story:** As a challenge author, I want a standardized challenge format, so that I can create new challenges consistently.

#### Acceptance Criteria

1. THE Platform SHALL store each challenge in a dedicated directory at /challenges/<name>/
2. THE Challenge_Definition SHALL include a Dockerfile defining the base container image
3. THE Challenge_Definition SHALL include a setup script that injects the specific fault
4. THE Challenge_Definition SHALL include a validate.sh script that checks if the issue is resolved
5. THE Challenge_Definition SHALL include a metadata.json file with title, difficulty, brief, and hints fields
6. WHEN the platform starts, THE Platform SHALL load all challenge definitions from the challenges directory

### Requirement 8: Starter Challenge Set

**User Story:** As a user, I want diverse realistic challenges, so that I practice different DevOps troubleshooting skills.

#### Acceptance Criteria

1. THE Platform SHALL include a challenge for debugging a Docker container restart loop
2. THE Platform SHALL include a challenge for resolving server disk full issues
3. THE Platform SHALL include a challenge for fixing Nginx 502 errors
4. THE Platform SHALL include a challenge for correcting broken GitHub Actions workflow YAML
5. THE Platform SHALL include a challenge for debugging Kubernetes CrashLoopBackOff pod failures

### Requirement 9: Leaderboard Ranking

**User Story:** As a user, I want to see how my completion times compare to others, so that I can gauge my troubleshooting speed.

#### Acceptance Criteria

1. THE Platform SHALL display a leaderboard page with user rankings
2. THE Platform SHALL rank users by challenge completion, then by completion time within each challenge
3. THE Platform SHALL display username and completion time for each leaderboard entry
4. THE Leaderboard SHALL update within 5 seconds after a user completes a challenge
5. THE Platform SHALL provide separate leaderboard views per challenge

### Requirement 10: Data Persistence

**User Story:** As a platform operator, I want user data and attempts stored reliably, so that progress is preserved across sessions.

#### Acceptance Criteria

1. THE Platform SHALL store user account data in a SQLite database
2. THE Platform SHALL store all challenge attempts with timestamps in the database
3. THE Platform SHALL store leaderboard data in the database
4. WHEN the platform restarts, THE Platform SHALL preserve all user data and challenge history
5. THE Platform SHALL enforce database schema integrity constraints

### Requirement 11: Session Security Constraints

**User Story:** As a platform operator, I want containers to have minimal privileges, so that I reduce security risks from user actions.

#### Acceptance Criteria

1. THE Session_Manager SHALL configure container filesystems as read-only where the challenge permits
2. THE Session_Manager SHALL prevent container access to the Docker socket
3. THE Session_Manager SHALL prevent container access to the host filesystem
4. THE Session_Manager SHALL apply resource quotas to prevent denial of service
5. WHEN a container attempts prohibited operations, THE Platform SHALL deny the operation and log the attempt

### Requirement 12: Frontend Application Structure

**User Story:** As a developer, I want a maintainable frontend architecture, so that I can extend features efficiently.

#### Acceptance Criteria

1. THE Frontend SHALL be built using React with Vite as the build tool
2. THE Frontend SHALL use Tailwind CSS for styling
3. THE Frontend SHALL use xterm.js for terminal rendering
4. THE Frontend SHALL organize code into logical component directories
5. THE Frontend SHALL implement type checking using PropTypes or TypeScript

### Requirement 13: Backend API Structure

**User Story:** As a developer, I want a well-structured backend API, so that I can add endpoints and maintain code quality.

#### Acceptance Criteria

1. THE Backend SHALL be built using FastAPI with Python
2. THE Backend SHALL support WebSocket connections for terminal communication
3. THE Backend SHALL use type hints for all function signatures
4. THE Backend SHALL organize code into logical module files
5. THE Backend SHALL implement input validation for all API endpoints

### Requirement 14: Container Management

**User Story:** As a developer, I want reliable container lifecycle management, so that resources are properly allocated and cleaned up.

#### Acceptance Criteria

1. THE Session_Manager SHALL use Docker SDK for Python for container operations
2. WHEN a session starts, THE Session_Manager SHALL create a container with the challenge image
3. WHEN a session ends normally, THE Session_Manager SHALL remove the container within 5 seconds
4. WHEN a session times out, THE Session_Manager SHALL forcefully stop and remove the container
5. THE Session_Manager SHALL track active containers and prevent resource leaks

### Requirement 15: Deployment Configuration

**User Story:** As a platform operator, I want a simple deployment process, so that I can run the platform on cloud infrastructure.

#### Acceptance Criteria

1. THE Platform SHALL provide a Docker Compose configuration file
2. THE Platform SHALL run on an AWS EC2 free-tier instance
3. THE Platform SHALL expose the frontend on a standard HTTP port
4. THE Platform SHALL configure container networking for frontend-backend communication
5. THE Platform SHALL persist the SQLite database using Docker volumes

### Requirement 16: CI/CD Pipeline

**User Story:** As a developer, I want automated testing and deployment, so that I maintain code quality and streamline releases.

#### Acceptance Criteria

1. THE Platform SHALL include a GitHub Actions workflow for continuous integration
2. THE Platform SHALL run linting checks on all code changes
3. THE Platform SHALL run unit tests on all code changes
4. THE Platform SHALL build Docker images for deployment
5. WHEN tests pass on the main branch, THE Platform SHALL trigger deployment to the EC2 instance

### Requirement 17: Session Manager Testing

**User Story:** As a developer, I want automated tests for session management, so that I prevent container lifecycle bugs.

#### Acceptance Criteria

1. THE Platform SHALL include unit tests for session creation logic
2. THE Platform SHALL include unit tests for session termination logic
3. THE Platform SHALL include unit tests for timeout enforcement
4. THE Platform SHALL include unit tests for resource limit configuration
5. THE Platform SHALL verify that all tests pass before deployment

### Requirement 18: Validator Testing

**User Story:** As a developer, I want automated tests for validation logic, so that I ensure challenges are verifiable correctly.

#### Acceptance Criteria

1. THE Platform SHALL include unit tests for validator execution
2. THE Platform SHALL include unit tests for validation result parsing
3. THE Platform SHALL include integration tests with sample challenge validation scripts
4. THE Platform SHALL verify successful validation detection
5. THE Platform SHALL verify failed validation detection with hint extraction

### Requirement 19: Documentation

**User Story:** As a developer or user, I want clear documentation, so that I can understand, deploy, and contribute to the platform.

#### Acceptance Criteria

1. THE Platform SHALL include a README.md file in the repository root
2. THE README SHALL include an architecture diagram using Mermaid syntax
3. THE README SHALL include setup instructions for local development
4. THE README SHALL include deployment instructions for production
5. THE README SHALL include a placeholder for a demo GIF

### Requirement 20: Project Structure Organization

**User Story:** As a developer, I want a clean folder structure, so that I can navigate the codebase efficiently.

#### Acceptance Criteria

1. THE Platform SHALL organize frontend code in a dedicated frontend directory
2. THE Platform SHALL organize backend code in a dedicated backend directory
3. THE Platform SHALL organize challenge definitions in a challenges directory
4. THE Platform SHALL organize tests adjacent to the code they test
5. THE Platform SHALL include configuration files at the repository root
