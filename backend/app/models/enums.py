"""
Enums for the healthcare diagnostic backend
"""

from enum import Enum


class HealthSpeciality(str, Enum):
    """Medical speciality enumeration"""
    SKIN = "skin"
    DENTAL = "dental"
    ORAL = "oral"


class MessageType(str, Enum):
    """Message type enumeration"""
    TEXT = "text"
    IMAGE = "image"


class ResponseStatus(str, Enum):
    """Response status enumeration"""
    RESPONSE = "response"
    WARNING = "warning"
    REPORT = "report"


class ChatStatus(str, Enum):
    """Chat status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


class Severity(str, Enum):
    """Severity level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UserRole(str, Enum):
    """User role enumeration"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class ImageFormat(str, Enum):
    """Supported image formats"""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"


class AnalysisType(str, Enum):
    """Analysis type enumeration"""
    SKIN_DISEASE = "skin_disease"
    ORAL_HEALTH = "oral_health"
    GENERAL_DERMATOLOGY = "general_dermatology"
