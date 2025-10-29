"""
Custom exceptions for the healthcare diagnostic backend
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class HealthcareDiagnosticException(Exception):
    """Base exception for healthcare diagnostic backend"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(HealthcareDiagnosticException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AuthenticationError(HealthcareDiagnosticException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(HealthcareDiagnosticException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ImageValidationError(HealthcareDiagnosticException):
    """Raised when image validation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class CVModelError(HealthcareDiagnosticException):
    """Raised when CV model processing fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class LLMServiceError(HealthcareDiagnosticException):
    """Raised when LLM service fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class StorageError(HealthcareDiagnosticException):
    """Raised when storage operations fail"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class SessionExpiredError(HealthcareDiagnosticException):
    """Raised when session has expired"""
    
    def __init__(self, message: str = "Session has expired"):
        super().__init__(
            message=message,
            status_code=status.HTTP_410_GONE
        )


class RateLimitExceededError(HealthcareDiagnosticException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class MedicalSafetyError(HealthcareDiagnosticException):
    """Raised when medical safety checks fail"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


def handle_healthcare_exception(exc: HealthcareDiagnosticException) -> HTTPException:
    """Convert custom exception to HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "details": exc.details
        }
    )
