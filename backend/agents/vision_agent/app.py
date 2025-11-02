"""
FastAPI Application for Vision Agent
Provides REST API endpoint for the LangGraph vision agent
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
import uvicorn
import os
from vision_agent import process_vision_request

app = FastAPI(
    title="Vision Agent API",
    description="LangGraph-based vision agent for medical image validation and prediction",
    version="1.0.0"
)


class VisionRequest(BaseModel):
    chat_id: str = Field(..., description="Chat document ID")
    chat_type: Literal["skin", "oral"] = Field(..., description="Type of medical image")
    
    class Config:
        schema_extra = {
            "example": {
                "chat_id": "9vEu1qRQ1lgphdnpN5mO",
                "chat_type": "skin"
            }
        }


class VisionResponse(BaseModel):
    chat_id: str
    chat_type: str
    is_valid: bool
    validation_reason: str
    prediction_result: Optional[dict] = None
    error: Optional[str] = None


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "service": "Vision Agent API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "gcp_project": os.getenv("GCP_PROJECT_ID", "not_set"),
        "location": os.getenv("GCP_LOCATION", "not_set")
    }


@app.post("/process", response_model=VisionResponse)
async def process_vision(request: VisionRequest):
    """
    Process a vision agent request
    
    - **chat_id**: The chat document ID to fetch image from
    - **chat_type**: Either "skin" or "oral" for validation
    
    Returns validation result and CV model prediction if valid
    """
    try:
        result = process_vision_request(
            chat_id=request.chat_id,
            chat_type=request.chat_type
        )
        return VisionResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Vision agent error: {str(e)}"
        )


@app.post("/validate-only", response_model=VisionResponse)
async def validate_only(request: VisionRequest):
    """
    Only validate image without getting prediction
    Useful for testing validation logic
    """
    try:
        from vision_agent import (
            get_most_recent_image,
            validate_image_with_gemini,
            VisionAgentState
        )
        
        # Get image
        image_path = get_most_recent_image(request.chat_id)
        if not image_path:
            return VisionResponse(
                chat_id=request.chat_id,
                chat_type=request.chat_type,
                is_valid=False,
                validation_reason="No image found for this chat_id",
                error="Image not found"
            )
        
        # Validate
        is_valid, reason = validate_image_with_gemini(image_path, request.chat_type)
        
        return VisionResponse(
            chat_id=request.chat_id,
            chat_type=request.chat_type,
            is_valid=is_valid,
            validation_reason=reason,
            prediction_result=None,
            error=None
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)