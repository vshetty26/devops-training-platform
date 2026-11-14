"""
Security middleware for adding security headers to all responses.

This module implements security headers to protect against common web vulnerabilities:
- Content Security Policy (CSP) to prevent XSS attacks
- X-Frame-Options to prevent clickjacking
- X-Content-Type-Options to prevent MIME sniffing
- X-XSS-Protection for legacy browser protection
- Strict-Transport-Security for HTTPS enforcement (production)

Requirements:
- 11.1, 11.2, 11.3, 11.4: Security constraints
- 14.1, 14.2, 14.3: Input validation and security
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.
    
    This middleware adds multiple security headers to protect against
    common web vulnerabilities including XSS, clickjacking, and MIME
    sniffing attacks.
    
    Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and add security headers to the response.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response with security headers added
        """
        response = await call_next(request)
        
        # Content Security Policy - Restrict resource loading to prevent XSS
        # In development, we're lenient. In production, this should be stricter.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        
        # X-Frame-Options - Prevent clickjacking by disallowing embedding in frames
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options - Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection - Enable browser XSS filter (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy - Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy - Restrict browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        # Note: Strict-Transport-Security (HSTS) should only be enabled in production
        # with HTTPS. Uncomment the line below when deploying with HTTPS:
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log security-relevant events.
    
    Logs authentication attempts, session operations, and other
    security-relevant activities for audit and monitoring.
    
    Requirements: 11.5
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Log security-relevant request information.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response from the next handler
        """
        # Log authentication and sensitive operations
        path = request.url.path
        method = request.method
        client_host = request.client.host if request.client else "unknown"
        
        # Log authentication attempts
        if path.startswith("/api/auth/"):
            logger.info(
                f"Auth request: {method} {path} from {client_host}"
            )
        
        # Log session operations
        elif path.startswith("/api/sessions"):
            logger.info(
                f"Session operation: {method} {path} from {client_host}"
            )
        
        # Process request
        response = await call_next(request)
        
        # Log failed authentication attempts (401 responses to auth endpoints)
        if path.startswith("/api/auth/") and response.status_code == 401:
            logger.warning(
                f"Failed authentication attempt: {method} {path} from {client_host}"
            )
        
        # Log forbidden access attempts
        if response.status_code == 403:
            logger.warning(
                f"Forbidden access attempt: {method} {path} from {client_host}"
            )
        
        return response
