# 🚀 DevOps Arena - Quick Start Guide

## Prerequisites Status

Based on your system, here's what you have:

✅ **Python 3.14.5** - Installed  
✅ **Node.js v24.4.1** - Installed  
✅ **npm 11.4.2** - Installed  
❌ **Docker** - NOT INSTALLED (Required!)
 
## Step 1: Install Docker Desktop

Docker is **required** to run the challenge containers.

### macOS Installation:

1. **Download Docker Desktop:**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Download Docker Desktop for Mac (Apple Silicon or Intel)

2. **Install:**
   - Open the downloaded `.dmg` file
   - Drag Docker to Applications folder
   - Launch Docker Desktop from Applications
   - Follow the setup wizard

3. **Verify Installation:**
   ```bash
   docker --version
   docker ps
   ```

   You should see the Docker version and an empty container list.

---

## Step 2: Set Up Backend (Terminal 1)

```bash
# Navigate to backend directory
cd /Users/vamshishetty/Desktop/Devops__Arena/backend

# Activate virtual environment (already exists)
source venv/bin/activate

# Install/update dependencies (if needed)
pip install -r requirements.txt

# Initialize database (run migrations)
python -c "from app.database import Base, engine; Base.metadata.create_all(engine)"

# Create a test user (optional)
python -c "
from app.database import SessionLocal
from app.services.auth_service import create_user
db = SessionLocal()
try:
    create_user(db, 'demo', 'demo123')
    print('✅ Created demo user: demo / demo123')
except:
    print('Demo user already exists')
finally:
    db.close()
"

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be available at:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

---

## Step 3: Build Challenge Docker Image (Terminal 2)

```bash
# Navigate to challenges directory
cd /Users/vamshishetty/Desktop/Devops__Arena/challenges/nginx-502

# Build the Docker image
docker build -t devops-arena-nginx-502:latest .

# Verify image was created
docker images | grep devops-arena
```

You should see: `devops-arena-nginx-502   latest`

---

## Step 4: Set Up Frontend (Terminal 3)

```bash
# Navigate to frontend directory
cd /Users/vamshishetty/Desktop/Devops__Arena/frontend

# Install dependencies (if not already installed)
npm install

# Start frontend dev server
npm run dev
```

**Frontend will be available at:** http://localhost:5173

---

## Step 5: Test the Application

### 5.1 Login
1. Open browser to http://localhost:5173
2. Login with:
   - Username: `demo`
   - Password: `demo123`

### 5.2 Start a Challenge
1. Click "Challenges" or navigate to http://localhost:5173/challenges
2. Click on "Fix Nginx 502 Bad Gateway"
3. Click "Start Challenge" button
4. Wait 5-10 seconds for container to provision

### 5.3 Use the Terminal
1. Terminal should appear and auto-connect
2. You should see a bash prompt
3. Try commands:
   ```bash
   ls -la
   pwd
   cat /challenge/setup.sh
   cat /tmp/broken_backend.conf
   ```

### 5.4 Debug the Challenge
The Nginx 502 challenge has a broken upstream configuration. To fix it:
```bash
# Check Nginx configuration
cat /tmp/broken_backend.conf

# You'll see upstream points to 127.0.0.1:9999 (doesn't exist)
# Fix it by serving static content directly or starting a backend

# Simple fix: Remove the broken config and restart nginx
sudo rm /tmp/broken_backend.conf
sudo nginx -s reload

# Or create a simple upstream
python3 -m http.server 9999 &
```

### 5.5 Validate Solution
1. Click "Check Solution" button
2. If correct, you'll see success message
3. Session will auto-terminate after validation

---

## Common Issues & Solutions

### Issue: "Connection refused" when starting session
**Solution:** Make sure Docker Desktop is running
```bash
docker ps  # Should work without errors
```

### Issue: "Image not found" error
**Solution:** Build the challenge Docker image first
```bash
cd challenges/nginx-502
docker build -t devops-arena-nginx-502:latest .
```

### Issue: Backend won't start - "Port 8000 in use"
**Solution:** Kill the process using port 8000
```bash
lsof -ti:8000 | xargs kill -9
```

### Issue: Frontend won't start - "Port 5173 in use"
**Solution:** Kill the process using port 5173
```bash
lsof -ti:5173 | xargs kill -9
```

### Issue: Terminal connects but no output
**Solution:** Check backend logs for errors
- Ensure WebSocket endpoint is working
- Verify container started successfully: `docker ps`

### Issue: "Cannot connect to Docker daemon"
**Solution:** Start Docker Desktop application

---

## Quick Commands Reference

### Check Services Status
```bash
# Backend
curl http://localhost:8000/api/challenges

# Frontend
curl http://localhost:5173

# Docker
docker ps
docker images | grep devops-arena
```

### View Logs
```bash
# Backend logs (in backend terminal)
# Logs appear automatically with --reload flag

# Frontend logs (in frontend terminal)
# Logs appear automatically

# Docker container logs
docker logs <container-id>
```

### Stop Everything
```bash
# Stop backend: Ctrl+C in Terminal 1
# Stop frontend: Ctrl+C in Terminal 3

# Stop all containers
docker ps -q | xargs docker stop

# Remove all stopped containers
docker ps -aq | xargs docker rm
```

---

## Development Workflow

### Making Changes

**Backend Changes:**
- Edit files in `backend/app/`
- Server auto-reloads (uvicorn --reload)
- Check Terminal 1 for errors

**Frontend Changes:**
- Edit files in `frontend/src/`
- Vite auto-reloads browser
- Check browser console for errors

**Challenge Changes:**
- Edit files in `challenges/nginx-502/`
- Rebuild Docker image:
  ```bash
  docker build -t devops-arena-nginx-502:latest challenges/nginx-502/
  ```

### Running Tests

**Backend Tests:**
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

**Frontend Tests:**
```bash
cd frontend
npm run test  # (if tests are added)
```

---

## Architecture Overview

```
Browser (localhost:5173)
    ↓ HTTP/WebSocket
Backend (localhost:8000)
    ↓ Docker SDK
Docker Daemon
    ↓ Creates/Manages
Challenge Container (nginx-502)
```

---

## Next Steps

Once everything is running:

1. ✅ Test authentication flow
2. ✅ Test challenge session creation
3. ✅ Test terminal connectivity
4. ✅ Debug and solve the challenge
5. ✅ Test solution validation

### Add More Challenges

To add new challenges:
1. Create directory in `challenges/`
2. Add Dockerfile, setup.sh, validate.sh, metadata.json
3. Build Docker image
4. Backend will auto-load on restart

---

## Troubleshooting Guide

### Full Reset

If everything is broken, do a full reset:

```bash
# 1. Stop all services (Ctrl+C in all terminals)

# 2. Stop and remove all containers
docker ps -aq | xargs docker rm -f

# 3. Remove DevOps Arena images
docker images | grep devops-arena | awk '{print $3}' | xargs docker rmi -f

# 4. Rebuild challenge images
cd challenges/nginx-502
docker build -t devops-arena-nginx-502:latest .

# 5. Reset database
cd backend
rm devops_arena.db
python -c "from app.database import Base, engine; Base.metadata.create_all(engine)"

# 6. Restart services (follow Steps 2-4 above)
```

---

## Contact & Support

For issues or questions:
- Check backend logs (Terminal 1)
- Check frontend console (Browser DevTools)
- Check Docker logs: `docker logs <container-id>`

---

**Status:** Ready for testing after Docker installation ✅

**Estimated Setup Time:** 15-20 minutes (including Docker installation)

