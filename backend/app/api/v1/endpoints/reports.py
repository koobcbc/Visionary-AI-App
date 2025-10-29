"""
Report generation and retrieval endpoints
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.v1.schemas.reports import (
    ReportRequest,
    ReportResponse,
    ReportListResponse,
    ReportStatus
)
from app.core.dependencies import get_current_user, rate_limiter_standard
from app.core.exceptions import StorageError, LLMServiceError
from app.services.llm.gemini_service import GeminiService
from app.services.storage.firestore_service import FirestoreService
from app.core.logging import log_api_request, log_api_response, log_error, log_medical_event

router = APIRouter()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limit: bool = Depends(rate_limiter_standard),
    llm_service: GeminiService = Depends(),
    firestore_service: FirestoreService = Depends()
):
    """
    Generate comprehensive diagnostic report
    """
    try:
        log_api_request(
            method="POST",
            path="/reports/generate",
            user_id=current_user["user_id"],
            chat_id=request.chat_id
        )
        
        # Get chat data
        chat_data = await firestore_service.get_chat_by_id(
            chat_id=request.chat_id,
            user_id=current_user["user_id"]
        )
        
        if not chat_data:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Check if CV analysis is available
        cv_result = chat_data.get("cv_result")
        if not cv_result:
            raise HTTPException(
                status_code=400, 
                detail="CV analysis required before generating report"
            )
        
        # Generate report using LLM
        report = await llm_service.generate_final_report(
            chat_data=chat_data,
            cv_result=cv_result,
            image_data=request.image_data
        )
        
        # Save report to Firestore
        report_id = await firestore_service.save_report(
            chat_id=request.chat_id,
            user_id=current_user["user_id"],
            report=report
        )
        
        log_medical_event(
            event_type="report_generated",
            details={
                "report_id": report_id,
                "disease_type": report.get("disease_type"),
                "follow_up_required": report.get("follow_up_required")
            },
            user_id=current_user["user_id"],
            chat_id=request.chat_id
        )
        
        log_api_response(
            method="POST",
            path="/reports/generate",
            status_code=200,
            response_time_ms=0,
            user_id=current_user["user_id"],
            chat_id=request.chat_id
        )
        
        return ReportResponse(
            report_id=report_id,
            chat_id=request.chat_id,
            report=report,
            status=ReportStatus.COMPLETED,
            message="Report generated successfully"
        )
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"], chat_id=request.chat_id)
        raise


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    firestore_service: FirestoreService = Depends()
):
    """
    Get specific report by ID
    """
    try:
        log_api_request(
            method="GET",
            path=f"/reports/{report_id}",
            user_id=current_user["user_id"]
        )
        
        report_data = await firestore_service.get_report_by_id(
            report_id=report_id,
            user_id=current_user["user_id"]
        )
        
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return ReportResponse(
            report_id=report_id,
            chat_id=report_data["chat_id"],
            report=report_data["report"],
            status=ReportStatus.COMPLETED,
            message="Report retrieved successfully"
        )
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"])
        raise


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    limit: int = 20,
    offset: int = 0,
    status: Optional[ReportStatus] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    firestore_service: FirestoreService = Depends()
):
    """
    List user's reports with pagination
    """
    try:
        log_api_request(
            method="GET",
            path="/reports/",
            user_id=current_user["user_id"]
        )
        
        reports = await firestore_service.list_user_reports(
            user_id=current_user["user_id"],
            limit=limit,
            offset=offset,
            status=status.value if status else None
        )
        
        total_count = await firestore_service.count_user_reports(
            user_id=current_user["user_id"],
            status=status.value if status else None
        )
        
        return ReportListResponse(
            reports=reports,
            total_count=total_count,
            limit=limit,
            offset=offset,
            message=f"Retrieved {len(reports)} reports"
        )
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"])
        raise


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    firestore_service: FirestoreService = Depends()
):
    """
    Delete a report
    """
    try:
        log_api_request(
            method="DELETE",
            path=f"/reports/{report_id}",
            user_id=current_user["user_id"]
        )
        
        success = await firestore_service.delete_report(
            report_id=report_id,
            user_id=current_user["user_id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"message": "Report deleted successfully"}
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"])
        raise
