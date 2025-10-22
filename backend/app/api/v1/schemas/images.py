"""
Image upload and analysis schemas
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.models.enums import HealthSpeciality


class ImageUploadRequest(BaseModel):
    """Request model for image upload"""
    image_url: str = Field(..., description="Image URL")
    speciality: HealthSpeciality = Field(..., description="Medical speciality")
    chat_id: Optional[str] = Field(default=None, description="Associated chat ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Image metadata")


class ImageUploadResponse(BaseModel):
    """Response model for image upload"""
    image_url: str = Field(..., description="Uploaded image URL")
    filename: str = Field(..., description="Original filename")
    speciality: HealthSpeciality = Field(..., description="Medical speciality")
    validated: bool = Field(..., description="Whether image passed validation")
    message: str = Field(..., description="Response message")


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis"""
    analysis_result: Dict[str, Any] = Field(..., description="CV model analysis result")
    speciality: HealthSpeciality = Field(..., description="Medical speciality")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence score")
    message: str = Field(..., description="Response message")


class ImageInfo(BaseModel):
    """Model for image information"""
    image_id: str = Field(..., description="Unique image identifier")
    filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="Image URL")
    speciality: HealthSpeciality = Field(..., description="Medical speciality")
    uploaded_at: str = Field(..., description="Upload timestamp")
    size_bytes: int = Field(..., description="Image size in bytes")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Image metadata")


class ImageValidationResult(BaseModel):
    """Model for image validation result"""
    is_valid: bool = Field(..., description="Whether image is valid")
    reason: Optional[str] = Field(default=None, description="Validation reason")
    suggestions: Optional[list] = Field(default=None, description="Improvement suggestions")
