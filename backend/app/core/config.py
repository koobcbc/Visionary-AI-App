"""
Configuration management for the healthcare diagnostic backend
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    APP_NAME: str = "Healthcare Diagnostic API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Healthcare Diagnostic Backend"
    
    # Google Cloud Configuration
    GCP_PROJECT_ID: str = Field(default=None, env="GCP_PROJECT_ID")
    GCP_CREDENTIALS_PATH: str = Field(default="./service-account.json", env="GCP_CREDENTIALS_PATH")
    GCS_BUCKET_NAME: str = Field(default="adsp-34002-ip07-visionary-ai.firebasestorage.app", env="GCS_BUCKET_NAME")
    
    # Firestore Collections
    FIRESTORE_COLLECTION_CHATS: str = "chats"
    FIRESTORE_COLLECTION_USERS: str = "users"
    FIRESTORE_COLLECTION_REPORTS: str = "reports"
    
    # CV Model Endpoints
    SKIN_CV_API: str = Field(
        default="https://skin-disease-cv-model-139431081773.us-central1.run.app/predict",
        env="SKIN_CV_API"
    )
    ORAL_CV_API: str = Field(default="", env="ORAL_CV_API")
    
    # Session Configuration
    SESSION_TIMEOUT_HOURS: int = Field(default=2, env="SESSION_TIMEOUT_HOURS")
    MAX_MESSAGES_PER_SESSION: int = Field(default=50, env="MAX_MESSAGES_PER_SESSION")
    
    # Image Validation
    MAX_IMAGE_SIZE_MB: int = Field(default=10, env="MAX_IMAGE_SIZE_MB")
    MIN_IMAGE_DIMENSION: int = Field(default=224, env="MIN_IMAGE_DIMENSION")
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        env="ALLOWED_IMAGE_TYPES"
    )
    
    # Security (simplified for capstone project)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "https://localhost:3000"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Firebase Configuration (set via environment variables for security)
    FIREBASE_API_KEY: Optional[str] = Field(default=None, env="FIREBASE_API_KEY")
    FIREBASE_AUTH_DOMAIN: Optional[str] = Field(default=None, env="FIREBASE_AUTH_DOMAIN")
    FIREBASE_PROJECT_ID: Optional[str] = Field(default=None, env="FIREBASE_PROJECT_ID")
    FIREBASE_STORAGE_BUCKET: Optional[str] = Field(default=None, env="FIREBASE_STORAGE_BUCKET")
    FIREBASE_MESSAGING_SENDER_ID: Optional[str] = Field(default=None, env="FIREBASE_MESSAGING_SENDER_ID")
    FIREBASE_APP_ID: Optional[str] = Field(default=None, env="FIREBASE_APP_ID")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
