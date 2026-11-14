"""
Application configuration using environment variables.

This module provides centralized configuration management for security-sensitive
settings including JWT secrets, CORS origins, and rate limiting.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Security-critical settings like JWT_SECRET_KEY should be set via
    environment variables in production. Development defaults are provided
    but should NEVER be used in production.
    """
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "dev-secret-key-change-in-production-use-env-var"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://frontend:5173",   # Docker Compose frontend service
    ]
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 5  # Max requests per minute for auth endpoints
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./devops_arena.db")
    
    # Session Configuration
    SESSION_TIMEOUT_SECONDS: int = 30 * 60  # 30 minutes
    
    # Container Security Configuration
    CONTAINER_CPU_LIMIT: float = 0.5  # 0.5 CPU cores
    CONTAINER_MEMORY_LIMIT: str = "256m"  # 256MB RAM
    CONTAINER_NETWORK_MODE: str = "none"  # No network access
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_cors_origins(self) -> List[str]:
        """
        Get CORS origins, optionally adding production origin from environment.
        
        Returns:
            List of allowed CORS origins
        """
        origins = self.CORS_ORIGINS.copy()
        
        # Add production origin if set
        production_origin = os.getenv("PRODUCTION_ORIGIN")
        if production_origin and production_origin not in origins:
            origins.append(production_origin)
        
        return origins
    
    def is_production(self) -> bool:
        """
        Check if running in production environment.
        
        Returns:
            True if production, False otherwise
        """
        return self.ENVIRONMENT.lower() == "production"


# Global settings instance
settings = Settings()
