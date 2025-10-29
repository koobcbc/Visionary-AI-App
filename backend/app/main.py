"""
Main FastAPI application for healthcare diagnostic backend
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.core.logging import logger, log_api_request, log_api_response, log_error
from app.core.exceptions import HealthcareDiagnosticException, handle_healthcare_exception
from app.api.v1.routes import api_router
from app.security.rate_limiter import rate_limiter


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        description="Production-ready healthcare diagnostic backend with AI-powered analysis",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint"""
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": time.time()
        }
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "Healthcare Diagnostic API",
            "version": settings.APP_VERSION,
            "docs": "/api/docs" if settings.DEBUG else "Documentation not available in production"
        }
    
    return app


def setup_middleware(app: FastAPI):
    """Setup middleware for the application"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure with actual domains in production
        )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log API requests and responses"""
        start_time = time.time()
        
        # Log request
        log_api_request(
            method=request.method,
            path=str(request.url.path),
            user_id=getattr(request.state, 'user_id', None),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log response
        log_api_response(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            response_time_ms=process_time * 1000,
            user_id=getattr(request.state, 'user_id', None),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return response
    
    # Rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Apply rate limiting"""
        try:
            # Get client identifier
            client_ip = request.client.host if request.client else "unknown"
            user_id = getattr(request.state, 'user_id', None)
            identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"
            
            # Check rate limit
            is_allowed, rate_info = rate_limiter.is_allowed(identifier, "standard")
            
            if not is_allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": rate_info.get("retry_after", 60)
                    },
                    headers={
                        "Retry-After": str(rate_info.get("retry_after", 60))
                    }
                )
            
            # Add rate limit info to response headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit_per_minute", 60))
            response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining_requests", 0))
            
            return response
            
        except Exception as e:
            log_error(e, context={"middleware": "rate_limiting"})
            # Fail open for safety
            return await call_next(request)


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers"""
    
    @app.exception_handler(HealthcareDiagnosticException)
    async def healthcare_exception_handler(request: Request, exc: HealthcareDiagnosticException):
        """Handle custom healthcare exceptions"""
        log_error(exc, context={"exception_type": "healthcare_diagnostic"})
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        log_error(exc, context={"exception_type": "general"})
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )


# Create the application instance
app = create_app()

# Log application startup
logger.info(f"🚀 Healthcare Diagnostic API v{settings.APP_VERSION} starting up")
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Debug mode: {settings.DEBUG}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
