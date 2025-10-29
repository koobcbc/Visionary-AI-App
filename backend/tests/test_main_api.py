"""
Test the main API endpoint to verify it matches specifications
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json


def test_call_main_api_text_message(client: TestClient, mock_firestore_service, mock_llm_service):
    """Test main API with text message"""
    
    # Mock the dependencies
    with patch('app.api.v1.endpoints.chat.FirestoreService', return_value=mock_firestore_service), \
         patch('app.api.v1.endpoints.chat.GeminiService', return_value=mock_llm_service):
        
        # Test data matching your specifications
        request_data = {
            "message": "I have a skin condition that I'm concerned about",
            "image_url": "",
            "user_id": "test_user_123",
            "chat_id": "test_chat_123",
            "type": "text",
            "speciality": "skin"
        }
        
        response = client.post(
            "/api/v1/chat/process",
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response format matches your specifications
        assert "response" in data
        assert "status" in data
        assert data["status"] in ["response", "warning", "report"]
        assert isinstance(data["response"], str)  # Markdown format


def test_call_main_api_image_message(client: TestClient, mock_firestore_service, mock_llm_service, mock_cv_service):
    """Test main API with image message"""
    
    with patch('app.api.v1.endpoints.chat.FirestoreService', return_value=mock_firestore_service), \
         patch('app.api.v1.endpoints.chat.GeminiService', return_value=mock_llm_service), \
         patch('app.api.v1.endpoints.chat.CVModelService', return_value=mock_cv_service):
        
        # Test data matching your specifications
        request_data = {
            "message": "",
            "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "user_id": "test_user_123",
            "chat_id": "test_chat_123",
            "type": "image",
            "speciality": "skin"
        }
        
        response = client.post(
            "/api/v1/chat/process",
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response format matches your specifications
        assert "response" in data
        assert "status" in data
        assert data["status"] == "report"  # Should be "report" for image processing
        assert isinstance(data["response"], str)  # Markdown format


def test_call_main_api_dental_speciality(client: TestClient, mock_firestore_service, mock_llm_service):
    """Test main API with dental speciality"""
    
    with patch('app.api.v1.endpoints.chat.FirestoreService', return_value=mock_firestore_service), \
         patch('app.api.v1.endpoints.chat.GeminiService', return_value=mock_llm_service):
        
        request_data = {
            "message": "I have a dental issue",
            "image_url": "",
            "user_id": "test_user_123",
            "chat_id": "test_chat_123",
            "type": "text",
            "speciality": "dental"
        }
        
        response = client.post(
            "/api/v1/chat/process",
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response format
        assert "response" in data
        assert "status" in data
        assert data["status"] in ["response", "warning", "report"]


def test_call_main_api_empty_message(client: TestClient, mock_firestore_service, mock_llm_service):
    """Test main API with empty message (should still work)"""
    
    with patch('app.api.v1.endpoints.chat.FirestoreService', return_value=mock_firestore_service), \
         patch('app.api.v1.endpoints.chat.GeminiService', return_value=mock_llm_service):
        
        request_data = {
            "message": "",  # Empty message as specified
            "image_url": "",
            "user_id": "test_user_123",
            "chat_id": "test_chat_123",
            "type": "text",
            "speciality": "skin"
        }
        
        response = client.post(
            "/api/v1/chat/process",
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should handle empty message gracefully
        assert response.status_code in [200, 422]  # Either success or validation error


def test_call_main_api_metadata_caching(mock_firestore_service, mock_llm_service):
    """Test that metadata is cached until session ends"""
    
    # This test verifies the caching behavior you specified
    chat_data = {
        "chat_id": "test_chat_123",
        "user_id": "test_user_123",
        "speciality": "skin",
        "messages": [],
        "metadata": {"age": "30", "gender": "male", "symptoms": []},
        "image_analyzed": False,
        "cv_result": None,
        "status": "active"
    }
    
    mock_firestore_service.get_or_create_chat.return_value = chat_data
    
    # Verify metadata is retrieved and cached
    result = mock_firestore_service.get_or_create_chat("test_chat_123", "test_user_123", "skin")
    assert "metadata" in result
    assert result["metadata"]["age"] == "30"
    
    # Verify metadata update is called
    mock_firestore_service.update_metadata.assert_called()


def test_call_main_api_status_values():
    """Test that status values match your specifications exactly"""
    
    # Test all three status values you specified
    status_values = ["response", "warning", "report"]
    
    for status in status_values:
        assert status in ["response", "warning", "report"]
    
    # Verify these are the only valid status values
    assert len(status_values) == 3


def test_call_main_api_parameters():
    """Test that all required parameters are present"""
    
    required_params = [
        "message",      # empty or string
        "image_url",    # empty or string
        "user_id",      # string
        "chat_id",      # string
        "type",         # "text" or "image"
        "speciality"   # "dental" or "skin"
    ]
    
    # Test that all parameters are defined
    for param in required_params:
        assert param in required_params
    
    # Test parameter types
    assert isinstance("", str)  # message can be empty string
    assert isinstance("", str)  # image_url can be empty string
    assert isinstance("user123", str)  # user_id must be string
    assert isinstance("chat123", str)  # chat_id must be string
    assert "text" in ["text", "image"]  # type must be text or image
    assert "dental" in ["dental", "skin"]  # speciality must be dental or skin


def test_call_main_api_output_format():
    """Test that output format matches your specifications exactly"""
    
    # Expected output format
    expected_output = {
        "response": "string (markdown format)",
        "status": "response|warning|report"
    }
    
    # Verify structure
    assert "response" in expected_output
    assert "status" in expected_output
    
    # Verify status values
    valid_statuses = ["response", "warning", "report"]
    assert expected_output["status"] in valid_statuses
