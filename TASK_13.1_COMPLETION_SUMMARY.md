# Task 13.1 Completion Summary: Docker Restart Loop Challenge

## Overview
Successfully created a new challenge that simulates a Docker container restart loop scenario. This challenge teaches users to debug and fix broken startup scripts that cause containers to exit immediately and repeatedly restart.

## Challenge Details

**Challenge ID**: docker-restart-loop  
**Title**: Fix Docker Container Restart Loop  
**Difficulty**: Easy  
**Location**: `/challenges/docker-restart-loop/`

## Files Created

### 1. Dockerfile
- **Base Image**: Ubuntu 22.04
- **Installed Packages**: Python3, curl, vim, procps
- **User Configuration**: Non-root user (challenger, UID 1000)
- **Structure**: Follows the same pattern as nginx-502 challenge
- **Purpose**: Provides the base container environment for the challenge

### 2. setup.sh (Fault Injection Script)
**Injected Fault**: Creates a broken startup script at `/app/start.sh` that:
- Checks for a non-existent configuration file (`/app/config.json`)
- Exits with error code 1 if the file doesn't exist (which it doesn't)
- This simulates a common Docker restart loop scenario where init scripts fail immediately

**Additional Setup**:
- Creates a simple Python HTTP server application (`/app/app.py`) that should run on port 8080
- Creates a systemd-style service file as reference (`/tmp/app.service`)
- Provides clear documentation in the script output explaining the problem

**Real-World Relevance**: This simulates common scenarios like:
- Missing configuration files
- Broken health checks in init scripts
- Environment variables not set
- Dependencies not available at startup

### 3. validate.sh (Solution Validation Script)
**Validation Logic**:
1. Checks if `/app/start.sh` exists and is executable
2. Starts the application in the background
3. Monitors the process for 5 seconds to ensure it stays alive
4. Verifies the application responds to HTTP requests on port 8080
5. Returns exit code 0 (success) only if both conditions are met

**Exit Conditions**:
- **Success (exit 0)**: Application runs continuously and serves HTTP 200 responses
- **Failure (exit 1)**: Application exits early OR doesn't respond on port 8080

**Hints Provided on Failure**:
- Points to the missing `/app/config.json` file
- Suggests two solution approaches: create the file OR fix the check
- Provides testing commands

### 4. metadata.json (Challenge Metadata)
**Fields**:
- **id**: "docker-restart-loop"
- **title**: "Fix Docker Container Restart Loop"
- **difficulty**: "easy"
- **brief**: Clear description of the problem scenario
- **hints**: Array of 5 progressive hints guiding users to the solution

**Progressive Hint Strategy**:
1. Location hint: Check /app/start.sh
2. Problem hint: Script checks for /app/config.json
3. Solution hint: Create the file OR modify the script
4. Testing hint: How to test the fix manually
5. Verification hint: How to verify the application works

## Solution Approaches

Users can solve this challenge in multiple ways:

### Solution 1: Create the Missing File (Quick Fix)
```bash
touch /app/config.json
```

### Solution 2: Fix the Startup Script (Proper Fix)
Edit `/app/start.sh` to remove or fix the problematic check:
```bash
# Remove the file check entirely
vim /app/start.sh
# OR make it non-fatal
# Change: exit 1
# To: echo "Warning: config not found, using defaults"
```

### Solution 3: Provide a Valid Config
```bash
echo '{}' > /app/config.json
```

## Requirements Coverage

This task satisfies the following requirements:

- **Requirement 8.1**: "THE Platform SHALL include a challenge for debugging a Docker container restart loop"
- **Requirement 7.1**: "THE Platform SHALL store each challenge in a dedicated directory at /challenges/<name>/"
- **Requirement 7.2**: "THE Challenge_Definition SHALL include a Dockerfile defining the base container image"
- **Requirement 7.3**: "THE Challenge_Definition SHALL include a setup script that injects the specific fault"
- **Requirement 7.4**: "THE Challenge_Definition SHALL include a validate.sh script that checks if the issue is resolved"
- **Requirement 7.5**: "THE Challenge_Definition SHALL include a metadata.json file with title, difficulty, brief, and hints fields"

## Design Alignment

The challenge follows the design document specifications:

1. **Challenge-as-code pattern**: All challenge logic is declarative and script-based
2. **Security-first approach**: Runs as non-root user (UID 1000)
3. **Validation contract**: Exit 0 for success, non-zero for failure with hints on stdout
4. **Progressive hints**: Guides users from problem identification to solution

## Testing Performed

✓ **Bash Syntax Validation**: All shell scripts validated with `bash -n`  
✓ **JSON Validation**: metadata.json validated with Python json.tool  
✓ **File Structure**: Verified all 4 required files present  
✓ **Consistency**: Compared structure with nginx-502 challenge template  

## Integration Notes

This challenge integrates seamlessly with the existing platform:

1. **Challenge Loader**: Will automatically discover this challenge on backend startup (Requirement 7.6)
2. **Session Manager**: Will use the Dockerfile to build/pull the image and run containers
3. **Setup Script**: Will be executed via Docker exec after container creation
4. **Validation Service**: Will execute validate.sh and parse results
5. **Frontend**: Will display the challenge in the challenge list with metadata

## Educational Value

This challenge teaches:

1. **Debugging skills**: How to identify why a container keeps restarting
2. **Log analysis**: Understanding container exit codes and logs
3. **Startup scripts**: Common patterns and anti-patterns in init scripts
4. **Problem-solving**: Multiple valid approaches to fix the issue
5. **Docker fundamentals**: Container lifecycle and restart policies

## Difficulty Justification

**Rated as "easy"** because:
- Problem is clearly stated and localized to one file
- Hints guide users directly to the issue
- Multiple simple solution paths available
- No complex debugging or multi-component troubleshooting required
- Good introductory challenge for the platform

## Next Steps

The challenge is ready for:
1. Docker image building (when Docker is available)
2. Integration testing with the session manager
3. End-to-end testing with the full platform
4. Deployment alongside other challenges

## Files Summary

```
challenges/docker-restart-loop/
├── Dockerfile          (774 bytes)
├── setup.sh           (1,991 bytes)
├── validate.sh        (1,651 bytes)
└── metadata.json      (849 bytes)
```

All files created successfully and follow the established challenge pattern from nginx-502.
