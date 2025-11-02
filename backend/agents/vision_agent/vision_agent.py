"""
Vision Agent for LangGraph Supervisor Architecture
Validates and processes medical images for skin and oral conditions
"""

from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import requests
import tempfile
import os


# State definition
class VisionAgentState(TypedDict):
    chat_id: str
    chat_type: Literal["skin", "oral"]
    image_path: Optional[str]
    is_valid: bool
    validation_reason: str
    prediction_result: Optional[dict]
    error: Optional[str]


# Configuration
BUCKET_NAME = "adsp-34002-ip07-visionary-ai.firebasestorage.app"
SKIN_CV_ENDPOINT = "https://skin-disease-cv-model-139431081773.us-central1.run.app/predict"
ORAL_CV_ENDPOINT = "https://oral-cancer-app-139431081773.us-central1.run.app"
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "adsp-34002-ip07-visionary-ai")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)


def get_most_recent_image(chat_id: str, bucket_name: str = BUCKET_NAME) -> Optional[str]:
    """Get most recent image from GCS for a chat"""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        prefix = f"chats/{chat_id}/"
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        if not blobs:
            print(f"No images found for chat_id: {chat_id}")
            return None
        
        most_recent_blob = max(blobs, key=lambda b: b.updated)
        gcs_path = f"gs://{bucket_name}/{most_recent_blob.name}"
        
        print(f"✓ Most recent image: {gcs_path}")
        print(f"  Updated at: {most_recent_blob.updated}")
        
        return gcs_path
    except Exception as e:
        print(f"ERROR getting image: {e}")
        return None


def validate_image_with_gemini(image_path: str, chat_type: str) -> tuple[bool, str]:
    """
    Use Gemini Vision to validate if image matches expected type
    
    Returns:
        (is_valid, reason)
    """
    try:
        model = GenerativeModel("gemini-2.5-pro")
        
        if chat_type == "skin":
            prompt = """Analyze this image and determine if it shows human skin or a skin-related condition.
            
Respond with ONLY a JSON object in this exact format:
{
    "is_valid": true/false,
    "reason": "Brief explanation of what you see and why it is or isn't a skin image"
}

The image is VALID if it shows:
- Human skin (any body part)
- Skin lesions, rashes, discolorations, or abnormalities
- Dermatological conditions

The image is INVALID if it shows:
- Mouth, teeth, gums, tongue, or oral cavity
- Other body parts without visible skin focus
- Non-medical or irrelevant content
- No human body parts"""
        else:  # oral
            prompt = """Analyze this image and determine if it shows the oral cavity, mouth, teeth, or oral-related conditions.
            
Respond with ONLY a JSON object in this exact format:
{
    "is_valid": true/false,
    "reason": "Brief explanation of what you see and why it is or isn't an oral/dental image"
}

The image is VALID if it shows:
- Teeth, gums, tongue, or oral cavity
- Dental conditions or abnormalities
- Mouth interior or lips (if showing oral health)

The image is INVALID if it shows:
- Skin conditions on body parts (not oral)
- Other body parts
- Non-medical or irrelevant content
- No human body parts"""
        
        # Determine mime type
        mime_type = "image/jpeg"
        if image_path.lower().endswith('.png'):
            mime_type = "image/png"
        elif image_path.lower().endswith('.webp'):
            mime_type = "image/webp"
        
        # Generate content
        response = model.generate_content([
            prompt,
            Part.from_uri(image_path, mime_type=mime_type)
        ])
        
        result_text = response.text.strip()
        print(f"Gemini response: {result_text}")
        
        # Parse JSON response
        import json
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        is_valid = result.get("is_valid", False)
        reason = result.get("reason", "No reason provided")
        
        print(f"✓ Validation result: {'VALID' if is_valid else 'INVALID'} - {reason}")
        return is_valid, reason
        
    except Exception as e:
        print(f"ERROR validating image: {e}")
        return False, f"Validation error: {str(e)}"


def get_cv_prediction(image_path: str, chat_type: str) -> Optional[dict]:
    """
    Get prediction from appropriate CV model API
    
    Args:
        image_path: GCS URI to image
        chat_type: "skin" or "oral"
    
    Returns:
        Prediction dictionary or None
    """
    try:
        # Parse GCS URI
        bucket_name = image_path.split("/")[2]
        blob_path = "/".join(image_path.split("/")[3:])
        
        # Download image locally
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            blob.download_to_filename(tmp.name)
            tmp_path = tmp.name
        
        try:
            # Select endpoint
            endpoint = SKIN_CV_ENDPOINT if chat_type == "skin" else ORAL_CV_ENDPOINT
            
            # Send to CV model
            with open(tmp_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(endpoint, files=files, timeout=30)
            
            if response.ok:
                result = response.json()
                print(f"✓ CV Prediction received: {result}")
                return result
            else:
                print(f"ERROR from CV model: {response.status_code} - {response.text}")
                return None
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        print(f"ERROR getting prediction: {e}")
        return None


# LangGraph Node Functions

def fetch_image_node(state: VisionAgentState) -> VisionAgentState:
    """Fetch most recent image from GCS"""
    print(f"\n=== Fetching Image ===")
    print(f"Chat ID: {state['chat_id']}, Type: {state['chat_type']}")
    
    image_path = get_most_recent_image(state['chat_id'])
    
    if not image_path:
        return {
            **state,
            "is_valid": False,
            "validation_reason": "No image found for this chat_id",
            "error": "Image not found"
        }
    
    return {
        **state,
        "image_path": image_path
    }


def validate_image_node(state: VisionAgentState) -> VisionAgentState:
    """Validate image matches chat_type using Gemini"""
    print(f"\n=== Validating Image ===")
    
    if state.get("error"):
        return state
    
    is_valid, reason = validate_image_with_gemini(
        state['image_path'],
        state['chat_type']
    )
    
    return {
        **state,
        "is_valid": is_valid,
        "validation_reason": reason
    }


def get_prediction_node(state: VisionAgentState) -> VisionAgentState:
    """Get prediction from CV model"""
    print(f"\n=== Getting CV Prediction ===")
    
    if not state['is_valid']:
        print("Skipping prediction - image not valid")
        return state
    
    prediction = get_cv_prediction(
        state['image_path'],
        state['chat_type']
    )
    
    if prediction is None:
        return {
            **state,
            "error": "Failed to get prediction from CV model"
        }
    
    return {
        **state,
        "prediction_result": prediction
    }


# Build the graph
def create_vision_agent_graph():
    """Create the LangGraph workflow"""
    workflow = StateGraph(VisionAgentState)
    
    # Add nodes
    workflow.add_node("fetch_image", fetch_image_node)
    workflow.add_node("validate_image", validate_image_node)
    workflow.add_node("get_prediction", get_prediction_node)
    
    # Add edges
    workflow.set_entry_point("fetch_image")
    workflow.add_edge("fetch_image", "validate_image")
    
    # Conditional routing after validation
    def route_after_validation(state: VisionAgentState) -> str:
        """Route to prediction or end based on validation"""
        if state['is_valid']:
            return "get_prediction"
        return END
    
    workflow.add_conditional_edges(
        "validate_image",
        route_after_validation,
        {
            "get_prediction": "get_prediction",
            END: END
        }
    )
    workflow.add_edge("get_prediction", END)
    
    return workflow.compile()


# Main execution function
def process_vision_request(chat_id: str, chat_type: Literal["skin", "oral"]) -> dict:
    """
    Process a vision agent request
    
    Args:
        chat_id: Chat document ID
        chat_type: Either "skin" or "oral"
    
    Returns:
        Result dictionary with validation and prediction
    """
    print(f"\n{'='*60}")
    print(f"VISION AGENT - Processing Request")
    print(f"{'='*60}")
    
    # Create initial state
    initial_state = VisionAgentState(
        chat_id=chat_id,
        chat_type=chat_type,
        image_path=None,
        is_valid=False,
        validation_reason="",
        prediction_result=None,
        error=None
    )
    
    # Create and run graph
    graph = create_vision_agent_graph()
    final_state = graph.invoke(initial_state)
    
    # Prepare response
    response = {
        "chat_id": final_state['chat_id'],
        "chat_type": final_state['chat_type'],
        "is_valid": final_state['is_valid'],
        "validation_reason": final_state['validation_reason'],
        "prediction_result": final_state.get('prediction_result'),
        "error": final_state.get('error')
    }
    
    print(f"\n{'='*60}")
    print(f"VISION AGENT - Complete")
    print(f"Valid: {response['is_valid']}")
    print(f"Reason: {response['validation_reason']}")
    if response['prediction_result']:
        print(f"Prediction: {response['prediction_result']}")
    print(f"{'='*60}\n")
    
    return response


if __name__ == "__main__":
    # Test the agent
    result = process_vision_request(
        chat_id="9vEu1qRQ1lgphdnpN5mO",
        chat_type="skin"
    )
    print("\nFinal Result:")
    print(result)