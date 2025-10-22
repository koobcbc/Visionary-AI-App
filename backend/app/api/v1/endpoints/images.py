"""
Image upload and processing endpoints
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse

from app.api.v1.schemas.images import (
    ImageUploadRequest,
    ImageUploadResponse,
    ImageAnalysisResponse,
    HealthSpeciality
)
from app.core.dependencies import get_current_user, rate_limiter_image_upload
from app.core.exceptions import ImageValidationError, CVModelError
from app.services.validation.image_validator import ImageValidator
from app.services.cv.cv_model_service import CVModelService
from app.services.storage.firestore_service import FirestoreService
from app.services.storage.gcs_service import GCSService
from app.core.logging import log_api_request, log_api_response, log_error, log_medical_event

router = APIRouter()


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    speciality: HealthSpeciality = HealthSpeciality.SKIN,
    chat_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limit: bool = Depends(rate_limiter_image_upload),
    image_validator: ImageValidator = Depends(),
    gcs_service: GCSService = Depends()
):
    """
    Upload and validate image for medical analysis
    """
    try:
        log_api_request(
            method="POST",
            path="/images/upload",
            user_id=current_user["user_id"],
            chat_id=chat_id
        )
        
        # Validate file type and size
        await image_validator.validate_file_properties(file)
        
        # Read file content
        image_data = await file.read()
        
        # Validate image content with AI
        is_valid, reason = await image_validator.validate_image_content(
            image_data=image_data,
            speciality=speciality.value
        )
        
        if not is_valid:
            raise ImageValidationError(
                message=f"Image validation failed: {reason}",
                details={"reason": reason, "speciality": speciality.value}
            )
        
        # Upload to GCS
        image_url = await gcs_service.upload_image(
            image_data=image_data,
            filename=file.filename,
            user_id=current_user["user_id"],
            speciality=speciality.value
        )
        
        log_medical_event(
            event_type="image_uploaded",
            details={
                "filename": file.filename,
                "speciality": speciality.value,
                "image_url": image_url
            },
            user_id=current_user["user_id"],
            chat_id=chat_id
        )
        
        log_api_response(
            method="POST",
            path="/images/upload",
            status_code=200,
            response_time_ms=0,
            user_id=current_user["user_id"],
            chat_id=chat_id
        )
        
        return ImageUploadResponse(
            image_url=image_url,
            filename=file.filename,
            speciality=speciality,
            validated=True,
            message="Image uploaded and validated successfully"
        )
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"], chat_id=chat_id)
        raise


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageUploadRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limit: bool = Depends(rate_limiter_image_upload),
    cv_service: CVModelService = Depends(),
    firestore_service: FirestoreService = Depends()
):
    """
    Analyze uploaded image using CV models
    """
    try:
        log_api_request(
            method="POST",
            path="/images/analyze",
            user_id=current_user["user_id"],
            chat_id=request.chat_id
        )
        
        # Download image data
        gcs_service = GCSService()
        image_data = await gcs_service.download_image(request.image_url)
        
        # Analyze with CV model
        if request.speciality == HealthSpeciality.SKIN:
            cv_result = await cv_service.analyze_skin_image(image_data)
        else:
            cv_result = await cv_service.analyze_oral_image(image_data)
        
        # Save CV result to Firestore
        if request.chat_id:
            await firestore_service.save_cv_result(
                chat_id=request.chat_id,
                cv_result=cv_result
            )
        
        log_medical_event(
            event_type="image_analyzed",
            details={
                "speciality": request.speciality.value,
                "cv_result": cv_result
            },
            user_id=current_user["user_id"],
            chat_id=request.chat_id
        )
        
        log_api_response(
            method="POST",
            path="/images/analyze",
            status_code=200,
            response_time_ms=0,
            user_id=current_user["user_id"],
            chat_id=request.chat_id
        )
        
        return ImageAnalysisResponse(
            analysis_result=cv_result,
            speciality=request.speciality,
            confidence=cv_result.get("confidence", 0.0),
            message="Image analysis completed successfully"
        )
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"], chat_id=request.chat_id)
        raise


@router.get("/{image_id}")
async def get_image_info(
    image_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    gcs_service: GCSService = Depends()
):
    """
    Get image information and metadata
    """
    try:
        log_api_request(
            method="GET",
            path=f"/images/{image_id}",
            user_id=current_user["user_id"]
        )
        
        image_info = await gcs_service.get_image_info(
            image_id=image_id,
            user_id=current_user["user_id"]
        )
        
        if not image_info:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return image_info
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"])
        raise


@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    gcs_service: GCSService = Depends()
):
    """
    Delete uploaded image
    """
    try:
        log_api_request(
            method="DELETE",
            path=f"/images/{image_id}",
            user_id=current_user["user_id"]
        )
        
        success = await gcs_service.delete_image(
            image_id=image_id,
            user_id=current_user["user_id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"message": "Image deleted successfully"}
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"])
        raise
