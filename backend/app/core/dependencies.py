"""
FastAPI dependencies for dependency injection (simplified for capstone project)
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
import logging

from app.core.config import settings
from app.services.storage.firestore_service import FirestoreService

logger = logging.getLogger(__name__)

# Firestore service instance
firestore_service = FirestoreService()


def get_current_user() -> dict:
    """
    Get current user (simplified for capstone project)
    """
    # For capstone project, return a mock user
    return {"user_id": "capstone_user_123", "email": "capstone@example.com"}


def get_firestore_service() -> FirestoreService:
    """
    Get Firestore service instance
    """
    return firestore_service


def get_current_user_optional() -> Optional[dict]:
    """
    Get current user (simplified for capstone project)
    """
    return get_current_user()


def verify_user_permissions(user: dict = Depends(get_current_user)) -> dict:
    """
    Verify user has necessary permissions (simplified for capstone project)
    """
    return user


def get_rate_limit_key(user: dict = Depends(get_current_user_optional)) -> str:
    """
    Get rate limiting key for user (simplified for capstone project)
    """
    return f"user:{user['user_id']}"


class RateLimiter:
    """
    Simple rate limiter dependency
    """
    def __init__(self, calls: int = 60, period: int = 60):
        self.calls = calls
        self.period = period
        self.clients = {}
    
    def __call__(self, key: str = Depends(get_rate_limit_key)):
        import time
        now = time.time()
        
        if key not in self.clients:
            self.clients[key] = []
        
        # Clean old calls
        self.clients[key] = [
            call_time for call_time in self.clients[key]
            if now - call_time < self.period
        ]
        
        if len(self.clients[key]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        self.clients[key].append(now)
        return True


# Rate limiter instances
rate_limiter_standard = RateLimiter(calls=60, period=60)
rate_limiter_strict = RateLimiter(calls=10, period=60)
rate_limiter_image_upload = RateLimiter(calls=5, period=60)
