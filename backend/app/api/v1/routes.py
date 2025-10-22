"""
API route aggregator for v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import chat, images, reports, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
