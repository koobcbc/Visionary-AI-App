"""
Chat request and response schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from app.models.enums import HealthSpeciality, MessageType, ResponseStatus


class ChatRequest(BaseModel):
    """Request model for chat processing"""
    message: Optional[str] = Field(default="", description="User text message")
    image_url: Optional[str] = Field(default="", description="Image URL or base64")
    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    chat_id: str = Field(..., min_length=1, description="Unique chat session ID")
    type: MessageType = Field(..., description="Message type: text or image")
    speciality: HealthSpeciality = Field(..., description="Medical speciality")
    
    @field_validator('image_url')
    @classmethod
    def validate_content(cls, v, info):
        """Ensure at least one field has content"""
        if not v:
            # Check if message is also empty
            values = info.data
            if not values.get('message'):
                raise ValueError("Either message or image_url must be provided")
        return v


class ChatResponse(BaseModel):
    """Response model for chat processing"""
    response: str = Field(..., description="AI response in markdown format")
    status: ResponseStatus = Field(..., description="Response status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    chat_id: str = Field(..., description="Chat session ID")
    messages: List[Dict[str, Any]] = Field(..., description="Chat messages")
    metadata: Dict[str, Any] = Field(..., description="Chat metadata")
    status: str = Field(..., description="Chat status")


class MessageCreate(BaseModel):
    """Model for creating a new message"""
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    role: str = Field(..., description="Message role (patient/assistant)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Message metadata")


class ChatCreate(BaseModel):
    """Model for creating a new chat"""
    speciality: HealthSpeciality = Field(..., description="Medical speciality")
    initial_message: Optional[str] = Field(default="", description="Initial message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Initial metadata")
