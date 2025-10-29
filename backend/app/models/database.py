"""
Database models for Firestore collections
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import HealthSpeciality, ChatStatus, Severity


class ChatMessage(BaseModel):
    """Model for chat messages"""
    role: str = Field(..., description="Message role (patient/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Message metadata")


class ChatMetadata(BaseModel):
    """Model for chat metadata"""
    age: Optional[str] = Field(default=None, description="Patient age")
    gender: Optional[str] = Field(default=None, description="Patient gender")
    symptoms: List[str] = Field(default=[], description="Reported symptoms")
    medical_history: Dict[str, Any] = Field(default={}, description="Medical history")
    location: Optional[str] = Field(default=None, description="Affected body location")
    duration: Optional[str] = Field(default=None, description="Symptom duration")


class ChatDocument(BaseModel):
    """Model for chat documents in Firestore"""
    chat_id: str = Field(..., description="Unique chat identifier")
    user_id: str = Field(..., description="User identifier")
    speciality: HealthSpeciality = Field(..., description="Medical speciality")
    messages: List[ChatMessage] = Field(default=[], description="Chat messages")
    metadata: ChatMetadata = Field(default_factory=ChatMetadata, description="Chat metadata")
    image_analyzed: bool = Field(default=False, description="Whether image has been analyzed")
    cv_result: Optional[Dict[str, Any]] = Field(default=None, description="CV analysis result")
    status: ChatStatus = Field(default=ChatStatus.ACTIVE, description="Chat status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")


class UserDocument(BaseModel):
    """Model for user documents in Firestore"""
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email")
    role: str = Field(default="patient", description="User role")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    preferences: Dict[str, Any] = Field(default={}, description="User preferences")
    medical_profile: Optional[Dict[str, Any]] = Field(default=None, description="Medical profile")


class ReportDocument(BaseModel):
    """Model for report documents in Firestore"""
    report_id: str = Field(..., description="Unique report identifier")
    chat_id: str = Field(..., description="Associated chat ID")
    user_id: str = Field(..., description="User identifier")
    report: Dict[str, Any] = Field(..., description="Report content")
    disease_type: Optional[str] = Field(default=None, description="Predicted disease type")
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    severity: Optional[Severity] = Field(default=None, description="Severity level")
    follow_up_required: bool = Field(default=False, description="Whether follow-up is required")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Report creation timestamp")
    reviewed_by: Optional[str] = Field(default=None, description="Reviewer ID")
    reviewed_at: Optional[datetime] = Field(default=None, description="Review timestamp")


class ImageDocument(BaseModel):
    """Model for image documents in Firestore"""
    image_id: str = Field(..., description="Unique image identifier")
    user_id: str = Field(..., description="User identifier")
    filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="Image URL")
    speciality: HealthSpeciality = Field(..., description="Medical speciality")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    size_bytes: int = Field(..., description="Image size in bytes")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Image metadata")
    analysis_result: Optional[Dict[str, Any]] = Field(default=None, description="Analysis result")
    validated: bool = Field(default=False, description="Whether image passed validation")
