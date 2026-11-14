from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, SessionLocal
from app.routers import auth, challenges, sessions, leaderboard
from app.services.challenge_loader import load_challenges
import uvicorn
import logging
import sys
from datetime import datetime

# Configure structured logging (Requirement 11.5)
def configure_logging():
    """
    Configure application-wide structured logging.
    
    Log Format: [timestamp] [level] [module] message
    Levels: DEBUG, INFO, WARNING, ERROR
    
    Requirements:
    - 11.5: Structured logging with levels for security and operational events
    """
    # Create formatter with timestamp, level, module, and message
    log_format = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for different modules
    logging.getLogger('app.services.session_manager').setLevel(logging.INFO)
    logging.getLogger('app.routers.auth').setLevel(logging.INFO)
    logging.getLogger('app.routers.sessions').setLevel(logging.INFO)
    logging.getLogger('app.services.auth_service').setLevel(logging.INFO)
    
    # Reduce noise from external libraries
    logging.getLogger('docker').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    
    logging.info("Structured logging configured successfully")

# Configure logging before creating app
configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevOps Arena API",
    description="Backend API for DevOps Arena challenge platform",
    version="0.0.1"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173", "https://*.vercel.app", "https://devops-training-platform.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(challenges.router, prefix="/api/challenges", tags=["challenges"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and load challenges on startup"""
    logger.info("Starting DevOps Arena API initialization")
    
    # Initialize database tables
    init_db()
    logger.info("Database initialized successfully")
    
    # Load challenges from filesystem
    db = SessionLocal()
    try:
        challenge_count = load_challenges(db)
        logger.info(f"Loaded {challenge_count} challenges from filesystem")
    except Exception as e:
        logger.error(f"Error loading challenges: {e}")
    finally:
        db.close()
    
    logger.info("DevOps Arena API started successfully")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "DevOps Arena API is running"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
