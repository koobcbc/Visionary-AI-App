"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.core.logging import log_api_request, log_api_response

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint
    """
    log_api_request(method="GET", path="/health/")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "service": "healthcare-diagnostic-backend"
    }
    
    log_api_response(
        method="GET",
        path="/health/",
        status_code=200,
        response_time_ms=0
    )
    
    return health_status


@router.get("/detailed")
async def detailed_health_check():
    """
    Detailed health check with service dependencies
    """
    log_api_request(method="GET", path="/health/detailed")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "service": "healthcare-diagnostic-backend",
        "dependencies": {
            "firestore": await _check_firestore_health(),
            "gcs": await _check_gcs_health(),
            "gemini": await _check_gemini_health(),
            "cv_models": await _check_cv_models_health()
        }
    }
    
    # Determine overall health
    all_healthy = all(
        dep["status"] == "healthy" 
        for dep in health_status["dependencies"].values()
    )
    
    health_status["status"] = "healthy" if all_healthy else "degraded"
    
    log_api_response(
        method="GET",
        path="/health/detailed",
        status_code=200,
        response_time_ms=0
    )
    
    return health_status


async def _check_firestore_health() -> Dict[str, Any]:
    """Check Firestore connectivity"""
    try:
        from app.services.storage.firestore_service import FirestoreService
        firestore_service = FirestoreService()
        await firestore_service.health_check()
        return {"status": "healthy", "message": "Connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def _check_gcs_health() -> Dict[str, Any]:
    """Check Google Cloud Storage connectivity"""
    try:
        from app.services.storage.gcs_service import GCSService
        gcs_service = GCSService()
        await gcs_service.health_check()
        return {"status": "healthy", "message": "Connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def _check_gemini_health() -> Dict[str, Any]:
    """Check Gemini API connectivity"""
    try:
        from app.services.llm.gemini_service import GeminiService
        llm_service = GeminiService()
        await llm_service.health_check()
        return {"status": "healthy", "message": "Connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


async def _check_cv_models_health() -> Dict[str, Any]:
    """Check CV models connectivity"""
    try:
        from app.services.cv.cv_model_service import CVModelService
        cv_service = CVModelService()
        await cv_service.health_check()
        return {"status": "healthy", "message": "Connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
