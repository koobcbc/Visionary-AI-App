import os
import json
from flask import Flask, request, jsonify
from vertexai.preview import generative_models
from vertexai import init
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, Optional

app = Flask(__name__)

# --- Configuration ---
# Initialize Vertex AI
init(project="adsp-34002-ip07-visionary-ai", location="us-central1")

# Initialize Firebase (only once)
if not firebase_admin._apps:
    # For Cloud Run, use default credentials or service account
    try:
        # Try to use service account file if provided
        firebase_key_path = os.environ.get("FIREBASE_KEY_PATH", "firebase_key.json")
        if os.path.exists(firebase_key_path):
            cred = credentials.Certificate(firebase_key_path)
            firebase_admin.initialize_app(cred)
        else:
            # Use default credentials on Cloud Run
            firebase_admin.initialize_app()
    except Exception as e:
        print(f"WARNING: Firebase initialization failed: {e}")

# --- Firebase/GCS Helper Functions ---
def get_most_recent_image(chat_id: str,
                          bucket_name: str = "adsp-34002-ip07-visionary-ai.firebasestorage.app") -> Optional[str]:
    """
    Get most recent image from GCS for a chat
    
    Args:
        chat_id: Chat document ID
        bucket_name: GCS bucket name
    
    Returns:
        GCS path to image or None
    """
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

def get_chat_metadata(chat_id: str) -> Dict:
    """
    Fetch metadata from Firestore for a chat
    
    Args:
        chat_id: Chat document ID
    
    Returns:
        Metadata dictionary
    """
    try:
        db = firestore.client()
        doc_ref = db.collection('chats').document(chat_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"No document found for chat_id: {chat_id}")
            return {}
        
        doc_data = doc.to_dict()
        metadata = doc_data.get('metadata', {})
        
        print(f"✓ Metadata retrieved for chat {chat_id}: {metadata}")
        return metadata
    except Exception as e:
        print(f"ERROR getting metadata: {e}")
        return {}

def get_chat_history_from_firestore(chat_id: str) -> list:
    """
    Fetch chat history from Firestore
    
    Args:
        chat_id: Chat document ID
    
    Returns:
        List of message dictionaries
    """
    try:
        db = firestore.client()
        doc_ref = db.collection('chats').document(chat_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"No chat history found for chat_id: {chat_id}")
            return []
        
        doc_data = doc.to_dict()
        messages = doc_data.get('messages', [])
        
        # Convert to standard format
        history = []
        for msg in messages:
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", "")
            })
        
        print(f"✓ Chat history retrieved: {len(history)} messages")
        return history
    except Exception as e:
        print(f"ERROR getting chat history: {e}")
        return []

def analyze_image_with_gemini(image_path: str) -> str:
    """
    Use Gemini Vision to analyze what's in the image using Vertex AI
    
    Args:
        image_path: GCS path to image (gs://bucket/path/to/image.jpg)
    
    Returns:
        Description of what's in the image
    """
    try:
        model = generative_models.GenerativeModel("gemini-2.0-flash-exp")
        
        prompt = "Describe in detail what you see in this image. Focus on any visible skin conditions, lesions, discolorations, or abnormalities if this is a dermatological image, or dental/oral conditions if this is an oral health image."
        
        # Determine mime type from file extension
        mime_type = "image/jpeg"
        if image_path.lower().endswith('.png'):
            mime_type = "image/png"
        elif image_path.lower().endswith('.webp'):
            mime_type = "image/webp"
        
        # Generate content using GCS URI
        response = model.generate_content([
            prompt,
            generative_models.Part.from_uri(image_path, mime_type=mime_type)
        ])
        
        description = response.text.strip()
        
        print(f"✓ Image analyzed: {description[:100]}...")
        return description
    except Exception as e:
        print(f"ERROR analyzing image: {e}")
        return f"Unable to analyze image: {str(e)}"

# --- Reporting Agent Personas ---
SKIN_DERMATOLOGY_PERSONA = """
You are a dermatology AI assistant specializing in skin conditions. Use the following data:
1. Chat history: {{history}}
2. Computer vision model output: {cv_result}
3. Image analysis: {image_description}
4. Uploaded skin image.

Generate a structured JSON output with ONLY these fields:
{
  "disease_type": "<Predicted disease or condition>",
  "disease_meaning_plain_english": "<Simple explanation of what it means>",
  "follow_up_required": "<Yes or No>",
  "home_remedy_enough": "<Yes or No>",
  "home_remedy_details": "<If Yes, describe safe remedies briefly>",
  "age": "<Extracted from user's chat history or metadata>",
  "gender": "<Extracted from user's chat history or metadata>",
  "symptoms": "<List key symptoms user mentioned>",
  "doctor_specialty": "<List which specialty of doctor patient should visit>",
  "other_information": "<Any other context the user shared>",
  "output": "<Single plain-English message for the user combining all the above info in clear, empathetic language. Do not mention confidence here.>"
}

Rules:
- Return ONLY valid JSON — no extra text or commentary.
- The 'output' field should summarize the key points clearly and concisely for the user.
- Use plain English and an empathetic tone.
- If confidence is low or disease uncertain, mark "follow_up_required": "Yes".
- If no home remedies are safe, set "home_remedy_enough": "No".
- Extract age and gender from metadata or chat history.
- Focus on skin-related conditions and dermatological issues.
"""

ORAL_DENTISTRY_PERSONA = """
You are a dental and oral health AI assistant specializing in teeth, gums, and oral cavity conditions. Use the following data:
1. Chat history: {{history}}
2. Computer vision model output: {cv_result}
3. Image analysis: {image_description}
4. Uploaded oral/dental image.

Generate a structured JSON output with ONLY these fields:
{
  "disease_type": "<Predicted dental/oral condition>",
  "disease_meaning_plain_english": "<Simple explanation of what it means>",
  "follow_up_required": "<Yes or No>",
  "home_remedy_enough": "<Yes or No>",
  "home_remedy_details": "<If Yes, describe safe remedies briefly>",
  "age": "<Extracted from user's chat history or metadata>",
  "gender": "<Extracted from user's chat history or metadata>",
  "symptoms": "<List key symptoms user mentioned>",
  "doctor_specialty": "<List which specialty of dentist/doctor patient should visit (e.g., General Dentist, Orthodontist, Periodontist, Oral Surgeon)>",
  "other_information": "<Any other context the user shared>",
  "output": "<Single plain-English message for the user combining all the above info in clear, empathetic language. Do not mention confidence here.>"
}

Rules:
- Return ONLY valid JSON — no extra text or commentary.
- The 'output' field should summarize the key points clearly and concisely for the user.
- Use plain English and an empathetic tone.
- If confidence is low or condition uncertain, mark "follow_up_required": "Yes".
- If no home remedies are safe, set "home_remedy_enough": "No".
- Extract age and gender from metadata or chat history.
- Focus on oral health, dental issues, gum diseases, and mouth-related conditions.
"""

def generate_report(chat_history: list, cv_result: dict, metadata: dict, 
                   image_path: str = None, chat_type: str = "skin") -> dict:
    """
    Generate a structured medical report using Gemini.
    
    Args:
        chat_history: List of conversation messages
        cv_result: Computer vision model output
        metadata: User metadata (age, gender, etc.)
        image_path: Path to the uploaded image
        chat_type: Type of consultation - "skin" or "oral"
    
    Returns:
        dict: Structured report
    """
    print(f"---REPORTING AGENT: Generating {chat_type} report...---")
    
    try:
        # Analyze image with Gemini Vision
        image_description = ""
        if image_path:
            print("📸 Analyzing image with Gemini Vision...")
            image_description = analyze_image_with_gemini(image_path)
        
        # Select persona based on chat_type
        if chat_type.lower() == "oral":
            persona = ORAL_DENTISTRY_PERSONA
            print("👨‍⚕️ Using ORAL/DENTAL persona")
        else:
            persona = SKIN_DERMATOLOGY_PERSONA
            print("👨‍⚕️ Using SKIN/DERMATOLOGY persona")
        
        model = generative_models.GenerativeModel(
            'gemini-2.0-flash-exp',
            system_instruction=persona
        )
        
        # Build the prompt
        prompt = f"""
Chat history:
{json.dumps(chat_history, indent=2)}

Computer vision model output:
{json.dumps(cv_result, indent=2)}

Image analysis (what Gemini sees in the image):
{image_description}

User metadata from Firestore:
{json.dumps(metadata, indent=2)}

Image path: {image_path if image_path else 'Not provided'}

Generate the structured JSON report following the exact format specified in your instructions.
Extract age, gender, and other information from the metadata and chat history provided above.
"""
        
        response = model.generate_content(prompt)
        report_text = response.text.strip()
        
        # Clean up markdown code blocks if present
        if report_text.startswith("```json"):
            report_text = report_text.replace("```json", "").replace("```", "").strip()
        elif report_text.startswith("```"):
            report_text = report_text.replace("```", "").strip()
        
        # Parse JSON
        report = json.loads(report_text)
        
        print(f"✓ Report generated successfully")
        return report
        
    except json.JSONDecodeError as je:
        print(f"ERROR: Invalid JSON response: {str(je)}")
        print(f"Raw response: {report_text[:500]}")
        raise ValueError(f"Report generation returned invalid JSON: {str(je)}")
    except Exception as e:
        print(f"ERROR: Report generation failed: {str(e)}")
        raise

@app.route("/generate_report", methods=["POST"])
def generate_report_endpoint():
    """
    Main API endpoint for the reporting agent.
    
    Expected JSON payload (Option 1 - Provide data directly):
    {
        "chat_type": "skin" or "oral",
        "chat_history": [...],
        "cv_result": {...},
        "metadata": {...},
        "image_path": "gs://..."
    }
    
    Expected JSON payload (Option 2 - Load from Firebase using chat_id):
    {
        "chat_type": "skin" or "oral",
        "chat_id": "9vEu1qRQ1lgphdnpN5mO",
        "cv_result": {...}
    }
    """
    try:
        data = request.get_json()
        
        # Validate request
        if not data:
            return jsonify({"error": "Request must be JSON"}), 400
        
        # Validate chat_type
        chat_type = data.get("chat_type", "skin").lower()
        if chat_type not in ["skin", "oral"]:
            return jsonify({
                "error": "chat_type must be either 'skin' or 'oral'"
            }), 400
        
        # Initialize variables
        chat_history_before = []
        
        # Check if chat_id is provided (Firebase mode)
        if "chat_id" in data:
            print(f"\n📥 Loading data from Firebase for chat_id: {data['chat_id']}")
            
            chat_id = data["chat_id"]
            cv_result = data.get("cv_result", {})
            
            if not cv_result:
                return jsonify({
                    "error": "cv_result is required when using chat_id"
                }), 400
            
            # Load data from Firebase/GCS
            print("📥 Fetching image from GCS...")
            image_path = get_most_recent_image(chat_id)
            
            print("📥 Fetching metadata from Firestore...")
            metadata = get_chat_metadata(chat_id)
            
            # Check if chat_history is provided in the request, otherwise fetch from Firestore
            if "chat_history" in data and data["chat_history"]:
                print("✓ Using chat_history from request payload")
                chat_history = data.get("chat_history", [])
                chat_history_before = chat_history.copy()
            else:
                print("📥 Fetching chat history from Firestore...")
                chat_history = get_chat_history_from_firestore(chat_id)
                # Store the original chat history from Firebase
                chat_history_before = chat_history.copy() if chat_history else []
            
        else:
            # Direct mode - data provided in request
            print("\n📥 Using data from request payload")
            
            required_fields = ["chat_history", "cv_result"]
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            chat_id = data.get("chat_id", "direct_mode")
            chat_history = data.get("chat_history", [])
            # Store the original chat history from request
            chat_history_before = chat_history.copy() if chat_history else []
            cv_result = data.get("cv_result", {})
            metadata = data.get("metadata", {})
            image_path = data.get("image_path")
        
        # Generate report
        print(f"\n🤖 Generating {chat_type} report with Gemini...")
        report = generate_report(chat_history, cv_result, metadata, image_path, chat_type)
        
        # Add the AI response to chat history
        chat_history_after = chat_history_before.copy() if chat_history_before else []
        chat_history_after.append({
            "role": "assistant",
            "content": report.get("output", ""),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Prepare image description
        image_description = ""
        if image_path:
            try:
                print("📸 Analyzing image for output...")
                image_description = analyze_image_with_gemini(image_path)
            except Exception as e:
                print(f"Warning: Could not analyze image: {e}")
                image_description = "Image analysis unavailable"
        
        # Return comprehensive output
        return jsonify({
            "status": "success",
            "generated_at": datetime.utcnow().isoformat(),
            "data_source": "firebase" if "chat_id" in data else "direct",
            
            # Input tracking
            "chat_type": chat_type,
            "chat_id": chat_id,
            "gcs_path": image_path,
            
            # Data used for generation
            "image_description": image_description,
            "metadata": metadata,
            "chat_history_before": chat_history_before,
            "cv_result": cv_result,
            
            # Generated report
            "report": report,
            
            # Updated chat history with AI response
            "chat_history_after": chat_history_after
        })
        
    except ValueError as ve:
        return jsonify({"error": str(ve), "status": "failed"}), 400
    except Exception as e:
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}",
            "status": "failed"
        }), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    firebase_status = "initialized" if firebase_admin._apps else "not initialized"
    
    return jsonify({
        "status": "healthy",
        "service": "medical-reporting-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "firebase": firebase_status,
        "supported_types": ["skin", "oral"]
    })

@app.route("/", methods=["GET"])
def root():
    """Root endpoint with API documentation"""
    return jsonify({
        "service": "Medical Reporting Agent (Skin & Oral)",
        "version": "3.0",
        "features": [
            "Firebase/Firestore integration",
            "GCS image retrieval",
            "Automatic metadata loading",
            "Structured medical reports",
            "Multi-specialty support (Dermatology & Dentistry)",
            "Gemini Vision image analysis via Vertex AI"
        ],
        "endpoints": {
            "/generate_report": "POST - Generate structured medical report",
            "/health": "GET - Health check"
        },
        "usage": {
            "option_1_firebase": {
                "description": "Load data from Firebase/GCS using chat_id",
                "example": {
                    "chat_type": "skin",
                    "chat_id": "9vEu1qRQ1lgphdnpN5mO",
                    "cv_result": {
                        "prediction": "Eczema",
                        "confidence": 0.87
                    }
                }
            },
            "option_2_direct": {
                "description": "Provide all data directly",
                "example": {
                    "chat_type": "oral",
                    "chat_history": [
                        {"role": "user", "content": "I have bleeding gums"}
                    ],
                    "cv_result": {
                        "prediction": "Gingivitis",
                        "confidence": 0.82
                    },
                    "metadata": {
                        "age": "28",
                        "gender": "male"
                    }
                }
            }
        },
        "chat_types": {
            "skin": "Dermatology consultation - skin conditions",
            "oral": "Dental/Oral health consultation - teeth, gums, mouth"
        }
    })

# --- Start Flask App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Medical Reporting Agent on port {port}")
    print(f"🔥 Firebase initialized: {bool(firebase_admin._apps)}")
    print(f"📋 Supported consultation types: skin, oral")
    app.run(host="0.0.0.0", port=port, debug=False)