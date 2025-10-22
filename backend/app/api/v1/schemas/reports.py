"""
Report generation and retrieval schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ReportStatus(str, Enum):
    """Report status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportRequest(BaseModel):
    """Request model for report generation"""
    chat_id: str = Field(..., description="Chat session ID")
    image_data: Optional[bytes] = Field(default=None, description="Image data for analysis")
    include_cv_analysis: bool = Field(default=True, description="Include CV analysis in report")
    include_metadata: bool = Field(default=True, description="Include chat metadata in report")


class ReportResponse(BaseModel):
    """Response model for report generation"""
    report_id: str = Field(..., description="Unique report identifier")
    chat_id: str = Field(..., description="Associated chat session ID")
    report: Dict[str, Any] = Field(..., description="Generated report content")
    status: ReportStatus = Field(..., description="Report status")
    message: str = Field(..., description="Response message")


class ReportListResponse(BaseModel):
    """Response model for report listing"""
    reports: List[Dict[str, Any]] = Field(..., description="List of reports")
    total_count: int = Field(..., description="Total number of reports")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")
    message: str = Field(..., description="Response message")


class ReportSummary(BaseModel):
    """Model for report summary"""
    report_id: str = Field(..., description="Report ID")
    chat_id: str = Field(..., description="Chat ID")
    disease_type: Optional[str] = Field(default=None, description="Predicted disease type")
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    follow_up_required: Optional[bool] = Field(default=None, description="Whether follow-up is required")
    created_at: datetime = Field(..., description="Report creation timestamp")
    status: ReportStatus = Field(..., description="Report status")


class DiagnosticReport(BaseModel):
    """Model for diagnostic report content"""
    disease_type: str = Field(..., description="Predicted condition")
    disease_meaning_plain_english: str = Field(..., description="Simple explanation")
    follow_up_required: str = Field(..., description="Yes or No")
    home_remedy_enough: str = Field(..., description="Yes or No")
    home_remedy_details: Optional[str] = Field(default=None, description="Safe remedies if applicable")
    age: Optional[str] = Field(default=None, description="Patient age")
    gender: Optional[str] = Field(default=None, description="Patient gender")
    symptoms: List[str] = Field(default=[], description="Reported symptoms")
    other_information: Optional[str] = Field(default=None, description="Additional context")
    output: str = Field(..., description="Final empathetic message for user")
    confidence_scores: Optional[Dict[str, float]] = Field(default=None, description="Confidence scores")
    recommendations: Optional[List[str]] = Field(default=None, description="Medical recommendations")
