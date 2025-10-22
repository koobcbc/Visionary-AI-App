"""
Test configuration and fixtures
"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from app.main import app
from app.core.config import settings
from app.services.storage.firestore_service import FirestoreService
from app.services.storage.gcs_service import GCSService
from app.services.llm.gemini_service import GeminiService
from app.services.cv.cv_model_service import CVModelService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_firestore_service():
    """Mock Firestore service"""
    mock_service = Mock(spec=FirestoreService)
    mock_service.get_or_create_chat = AsyncMock(return_value={
        "chat_id": "test_chat_123",
        "user_id": "test_user_123",
        "speciality": "skin",
        "messages": [],
        "metadata": {"age": "30", "gender": "male", "symptoms": []},
        "image_analyzed": False,
        "cv_result": None,
        "status": "active",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "expires_at": "2024-01-01T02:00:00"
    })
    mock_service.add_message = AsyncMock()
    mock_service.update_metadata = AsyncMock()
    mock_service.save_cv_result = AsyncMock()
    mock_service.save_report = AsyncMock(return_value="report_123")
    mock_service.health_check = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def mock_gcs_service():
    """Mock GCS service"""
    mock_service = Mock(spec=GCSService)
    mock_service.upload_image = AsyncMock(return_value="https://storage.googleapis.com/test-bucket/test-image.jpg")
    mock_service.download_image = AsyncMock(return_value=b"fake_image_data")
    mock_service.get_image_info = AsyncMock(return_value={
        "image_id": "test_image_123",
        "filename": "test.jpg",
        "url": "https://storage.googleapis.com/test-bucket/test-image.jpg",
        "speciality": "skin",
        "uploaded_at": "2024-01-01T00:00:00",
        "size_bytes": 1024
    })
    mock_service.delete_image = AsyncMock(return_value=True)
    mock_service.health_check = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def mock_llm_service():
    """Mock LLM service"""
    mock_service = Mock(spec=GeminiService)
    mock_service.chat_with_context = AsyncMock(return_value={
        "response": "This is a test response from the AI.",
        "status": "response",
        "extracted_metadata": {"age": "30"},
        "should_request_image": False
    })
    mock_service.generate_final_report = AsyncMock(return_value={
        "disease_type": "Test Condition",
        "disease_meaning_plain_english": "A test condition for testing purposes",
        "follow_up_required": "Yes",
        "home_remedy_enough": "No",
        "home_remedy_details": "",
        "age": "30",
        "gender": "male",
        "symptoms": ["test_symptom"],
        "other_information": "Test information",
        "output": "This is a test diagnostic report."
    })
    mock_service.validate_image_content = AsyncMock(return_value=(True, "Image validation passed"))
    mock_service.health_check = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def mock_cv_service():
    """Mock CV service"""
    mock_service = Mock(spec=CVModelService)
    mock_service.analyze_skin_image = AsyncMock(return_value={
        "predicted_class": "Test Skin Condition",
        "confidence": 0.85,
        "disease_type": "Test Skin Condition",
        "severity": "medium",
        "description": "A test skin condition",
        "recommendations": ["Test recommendation"],
        "model_version": "1.0",
        "analysis_timestamp": "2024-01-01T00:00:00"
    })
    mock_service.analyze_oral_image = AsyncMock(return_value={
        "predicted_class": "Test Oral Condition",
        "confidence": 0.80,
        "condition_type": "Test Oral Condition",
        "severity": "low",
        "description": "A test oral condition",
        "recommendations": ["Test recommendation"],
        "model_version": "1.0",
        "analysis_timestamp": "2024-01-01T00:00:00"
    })
    mock_service.health_check = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def sample_chat_request():
    """Sample chat request data"""
    return {
        "message": "I have a skin condition that I'm concerned about",
        "image_url": "",
        "user_id": "test_user_123",
        "chat_id": "test_chat_123",
        "type": "text",
        "speciality": "skin"
    }


@pytest.fixture
def sample_image_request():
    """Sample image upload request data"""
    return {
        "image_url": "https://storage.googleapis.com/test-bucket/test-image.jpg",
        "speciality": "skin",
        "chat_id": "test_chat_123",
        "metadata": {"filename": "test.jpg", "size": 1024}
    }


@pytest.fixture
def sample_report_request():
    """Sample report generation request data"""
    return {
        "chat_id": "test_chat_123",
        "image_data": b"fake_image_data",
        "include_cv_analysis": True,
        "include_metadata": True
    }


@pytest.fixture
def sample_user_context():
    """Sample user context"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "role": "patient"
    }


@pytest.fixture
def sample_cv_result():
    """Sample CV analysis result"""
    return {
        "predicted_class": "Test Skin Condition",
        "confidence": 0.85,
        "disease_type": "Test Skin Condition",
        "severity": "medium",
        "description": "A test skin condition",
        "recommendations": ["Test recommendation"],
        "model_version": "1.0",
        "analysis_timestamp": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_chat_data():
    """Sample chat data"""
    return {
        "chat_id": "test_chat_123",
        "user_id": "test_user_123",
        "speciality": "skin",
        "messages": [
            {
                "role": "patient",
                "content": "I have a skin condition that I'm concerned about",
                "timestamp": "2024-01-01T00:00:00",
                "metadata": {}
            }
        ],
        "metadata": {
            "age": "30",
            "gender": "male",
            "symptoms": ["concern"],
            "medical_history": {}
        },
        "image_analyzed": False,
        "cv_result": None,
        "status": "active",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "expires_at": "2024-01-01T02:00:00"
    }


@pytest.fixture
def sample_report_data():
    """Sample report data"""
    return {
        "report_id": "report_123",
        "chat_id": "test_chat_123",
        "user_id": "test_user_123",
        "report": {
            "disease_type": "Test Condition",
            "disease_meaning_plain_english": "A test condition for testing purposes",
            "follow_up_required": "Yes",
            "home_remedy_enough": "No",
            "home_remedy_details": "",
            "age": "30",
            "gender": "male",
            "symptoms": ["test_symptom"],
            "other_information": "Test information",
            "output": "This is a test diagnostic report."
        },
        "disease_type": "Test Condition",
        "confidence": 0.85,
        "follow_up_required": True,
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_auth_token():
    """Mock authentication token"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwicm9sZSI6InBhdGllbnQifQ.test_signature"


@pytest.fixture
def mock_image_data():
    """Mock image data"""
    return b"fake_image_data_for_testing"


@pytest.fixture
def mock_metadata():
    """Mock metadata"""
    return {
        "age": "30",
        "gender": "male",
        "symptoms": ["pain", "swelling"],
        "location": "arm",
        "duration": "2 weeks",
        "medical_history": {
            "diabetes": True,
            "hypertension": False
        }
    }


# Test configuration
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Set test environment variables
    settings.ENVIRONMENT = "test"
    settings.DEBUG = True
    yield
    # Cleanup after tests
    pass
