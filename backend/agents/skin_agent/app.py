# =============================================================================
# FILE: app.py - Flask API for Skin Specialist Agent (Optimized)
# =============================================================================

import os
import json
from flask import Flask, request, jsonify
from typing import TypedDict, Annotated, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from vertexai.preview import generative_models
from vertexai import init

app = Flask(__name__)

# Initialize Vertex AI
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "adsp-34002-ip07-visionary-ai")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
init(project=PROJECT_ID, location=LOCATION)

# =============================================================================
# STATE DEFINITION
# =============================================================================

class DermatologyState(TypedDict):
    """State for the dermatology consultation workflow"""
    chat_history: Annotated[list, "Chat history in standard format"]
    age: Annotated[str, "Patient's age"]
    gender: Annotated[str, "Patient's gender"]
    skin_cancer_history: Annotated[str, "Personal skin cancer history"]
    family_cancer_history: Annotated[str, "Family cancer history"]
    body_region: Annotated[str, "Body region of concern"]
    symptoms: Annotated[dict, "Symptoms (itch, hurt, grow, change, bleed)"]
    duration: Annotated[str, "How long the condition has been present"]
    other_information: Annotated[str, "Any other relevant information"]
    information_complete: Annotated[bool, "Whether all required info is collected"]
    next_action: Annotated[str, "Next action to take"]
    current_response: Annotated[str, "Current agent response"]
    should_end: Annotated[bool, "Whether to end the conversation"]

# =============================================================================
# COMBINED AGENT FUNCTION (SINGLE API CALL)
# =============================================================================

def process_user_message_combined(state: DermatologyState, user_message: str) -> DermatologyState:
    """
    Process user message with a SINGLE Gemini API call that:
    1. Extracts information
    2. Assesses completeness
    3. Generates next question or image request
    """
    model = generative_models.GenerativeModel("gemini-2.0-flash-exp")
    
    # Format chat history for context
    chat_context = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in state.get('chat_history', [])[-5:]
    ])
    
    combined_prompt = f"""
You are a dermatology AI assistant. Process the user's message in ONE response.

CURRENT PATIENT INFORMATION:
- Age: {state.get('age', 'Not provided')}
- Gender: {state.get('gender', 'Not provided')}
- Skin cancer history: {state.get('skin_cancer_history', 'Not provided')}
- Family cancer history: {state.get('family_cancer_history', 'Not provided')}
- Body region: {state.get('body_region', 'Not provided')}
- Symptoms: {json.dumps(state.get('symptoms', {}), indent=2)}
- Duration: {state.get('duration', 'Not provided')}
- Other info: {state.get('other_information', 'Not provided')}

RECENT CONVERSATION:
{chat_context}

USER'S LATEST MESSAGE: "{user_message}"

TASK: Return a JSON object with three sections:

1. EXTRACTED_INFO: Extract any new information from the user's message
2. ASSESSMENT: Determine if we have enough information
3. RESPONSE: Generate the appropriate response (question or image request)

REQUIRED INFORMATION:
- Age (must have)
- Gender (must have)
- Body region (must have)
- At least one symptom: itch, hurt, grow, change, bleed (must have at least one)

OPTIONAL INFORMATION:
- Skin cancer history
- Family cancer history
- Duration

Return ONLY this JSON structure:
{{
    "extracted_info": {{
        "age": "<age if mentioned, else null>",
        "gender": "<gender if mentioned, else null>",
        "skin_cancer_history": "<yes/no/unknown if mentioned, else null>",
        "family_cancer_history": "<yes/no/unknown if mentioned, else null>",
        "body_region": "<body region if mentioned, else null>",
        "symptoms": {{
            "itch": "<yes/no if mentioned, else null>",
            "hurt": "<yes/no if mentioned, else null>",
            "grow": "<yes/no if mentioned, else null>",
            "change": "<yes/no if mentioned, else null>",
            "bleed": "<yes/no if mentioned, else null>"
        }},
        "duration": "<duration if mentioned, else null>",
        "other_information": "<any other relevant info, else null>"
    }},
    "assessment": {{
        "information_complete": <true if all required fields present, else false>,
        "missing_required": ["<list of missing required fields>"],
        "has_symptoms": <true if at least one symptom answered, else false>
    }},
    "response": {{
        "type": "<'question' if more info needed, 'image_request' if complete>",
        "message": "<Either next question OR image upload request message>",
        "should_end": <true if image_request, else false>
    }}
}}

RESPONSE GUIDELINES:
- For questions: Ask about ONE missing field at a time, be empathetic and conversational
- For image request: Thank patient, summarize key concerns, ask for clear photo with tips
- Keep all messages warm and professional
"""
    
    try:
        response = model.generate_content(combined_prompt)
        result_text = response.text.strip()
        
        # Clean up markdown
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "").strip()
        
        result = json.loads(result_text)
        
        # 1. Update extracted information
        extracted = result.get('extracted_info', {})
        if extracted.get('age'):
            state['age'] = extracted['age']
        if extracted.get('gender'):
            state['gender'] = extracted['gender']
        if extracted.get('skin_cancer_history'):
            state['skin_cancer_history'] = extracted['skin_cancer_history']
        if extracted.get('family_cancer_history'):
            state['family_cancer_history'] = extracted['family_cancer_history']
        if extracted.get('body_region'):
            state['body_region'] = extracted['body_region']
        if extracted.get('duration'):
            state['duration'] = extracted['duration']
        if extracted.get('other_information'):
            current_other = state.get('other_information', '')
            state['other_information'] = f"{current_other}\n{extracted['other_information']}".strip()
        
        # Update symptoms
        if extracted.get('symptoms'):
            current_symptoms = state.get('symptoms', {})
            for symptom, value in extracted['symptoms'].items():
                if value is not None:
                    current_symptoms[symptom] = value
            state['symptoms'] = current_symptoms
        
        # 2. Update assessment
        assessment = result.get('assessment', {})
        state['information_complete'] = assessment.get('information_complete', False)
        
        # 3. Update response
        response_data = result.get('response', {})
        state['current_response'] = response_data.get('message', '')
        state['should_end'] = response_data.get('should_end', False)
        state['next_action'] = 'request_image' if state['should_end'] else 'ask_question'
        
        print(f"✓ Processed in single API call")
        print(f"  Information complete: {state['information_complete']}")
        print(f"  Should end: {state['should_end']}")
        
    except Exception as e:
        print(f"⚠️ Processing failed: {e}")
        # Fallback response
        state['current_response'] = "I'm here to help. Could you tell me more about your concern?"
        state['information_complete'] = False
        state['should_end'] = False
    
    return state

# =============================================================================
# WORKFLOW NODES
# =============================================================================

def combined_processing_node(state: DermatologyState) -> DermatologyState:
    """Single node that does all processing in one API call"""
    chat_history = state.get('chat_history', [])
    
    if chat_history:
        # Get last user message
        last_user_message = next(
            (msg['content'] for msg in reversed(chat_history) if msg['role'] == 'user'),
            None
        )
        
        if last_user_message:
            state = process_user_message_combined(state, last_user_message)
    
    return state

def router(state: DermatologyState) -> Literal["end"]:
    """Router: Always end after processing (single turn per invoke)"""
    return "end"

# =============================================================================
# BUILD WORKFLOW
# =============================================================================

def create_dermatology_workflow():
    """Create the optimized LangGraph workflow"""
    
    workflow = StateGraph(DermatologyState)
    
    # Single processing node
    workflow.add_node("process", combined_processing_node)
    
    # Simple flow: process → end
    workflow.set_entry_point("process")
    workflow.add_edge("process", END)
    
    # Compile with memory
    memory = MemorySaver()
    app_workflow = workflow.compile(checkpointer=memory)
    
    return app_workflow

# Initialize workflow
workflow = create_dermatology_workflow()

# =============================================================================
# FLASK API ENDPOINTS
# =============================================================================

@app.route("/", methods=["GET"])
def root():
    """Root endpoint with API documentation"""
    return jsonify({
        "service": "Skin Specialist Agent (Optimized)",
        "version": "2.0",
        "description": "LangGraph-based dermatology consultation agent with single-call optimization",
        "endpoints": {
            "/start": "POST - Start a new consultation",
            "/chat": "POST - Send a message in an existing consultation",
            "/state": "GET - Get current state of a consultation",
            "/health": "GET - Health check"
        },
        "features": [
            "Standard chat_history format",
            "Optimized: Single API call per message",
            "Stateful conversations with thread management",
            "Intelligent question generation",
            "Automatic image request when ready"
        ],
        "optimization": "Combines extraction + assessment + generation in ONE Gemini call"
    })

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "skin-specialist-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "project": PROJECT_ID,
        "location": LOCATION,
        "optimization": "single-call-mode"
    })

@app.route("/start", methods=["POST"])
def start_consultation():
    """
    Start a new consultation
    
    Expected JSON (optional):
    {
        "thread_id": "custom_thread_id",
        "chat_history": []  // Optional: provide existing chat history
    }
    
    Returns:
    {
        "thread_id": "...",
        "chat_history": [...],
        "response": "...",
        "collected_info": {...}
    }
    """
    try:
        data = request.get_json() or {}
        thread_id = data.get("thread_id") or f"consultation_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Check if chat_history is provided
        existing_chat_history = data.get("chat_history", [])
        
        initial_message = "Hello! I'm here to help you with your skin concern. To provide the best assistance, could you please tell me your age and gender?"
        
        # Initialize chat_history with first assistant message
        if not existing_chat_history:
            chat_history = [
                {
                    "role": "assistant",
                    "content": initial_message
                }
            ]
        else:
            chat_history = existing_chat_history
        
        return jsonify({
            "status": "success",
            "thread_id": thread_id,
            "chat_history": chat_history,
            "response": initial_message,
            "information_complete": False,
            "should_request_image": False,
            "collected_info": {
                "age": "",
                "gender": "",
                "body_region": "",
                "symptoms": {},
                "skin_cancer_history": "",
                "family_cancer_history": "",
                "duration": "",
                "other_information": ""
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/chat", methods=["POST"])
def chat():
    """
    Send a message in an existing consultation
    
    Expected JSON:
    {
        "thread_id": "...",
        "message": "I'm 45 years old, male",
        "chat_history": [...]  // Optional: provide current chat history
    }
    
    Returns:
    {
        "thread_id": "...",
        "chat_history": [...],  // Updated with new messages
        "response": "...",
        "information_complete": true/false,
        "should_request_image": true/false,
        "collected_info": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "error": "Request must be JSON"}), 400
        
        thread_id = data.get("thread_id")
        user_message = data.get("message")
        provided_chat_history = data.get("chat_history")
        
        if not thread_id or not user_message:
            return jsonify({
                "status": "error",
                "error": "Both 'thread_id' and 'message' are required"
            }), 400
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state or initialize
        try:
            current_state = workflow.get_state(config).values
        except:
            current_state = {
                "chat_history": provided_chat_history if provided_chat_history else [],
                "age": "",
                "gender": "",
                "skin_cancer_history": "",
                "family_cancer_history": "",
                "body_region": "",
                "symptoms": {},
                "duration": "",
                "other_information": "",
                "information_complete": False,
                "next_action": "ask_question",
                "current_response": "",
                "should_end": False
            }
        
        # If chat_history provided in request, use it (allows external state management)
        if provided_chat_history:
            current_state["chat_history"] = provided_chat_history
        
        # Add user message to chat_history
        current_state["chat_history"].append({
            "role": "user",
            "content": user_message
        })
        
        # Run the workflow (single API call happens here)
        result = workflow.invoke(current_state, config)
        
        # Get agent's response
        agent_response = result.get("current_response", "")
        
        # Add agent response to chat_history
        result["chat_history"].append({
            "role": "assistant",
            "content": agent_response
        })
        
        return jsonify({
            "status": "success",
            "thread_id": thread_id,
            "chat_history": result["chat_history"],
            "response": agent_response,
            "information_complete": result.get("information_complete", False),
            "should_request_image": result.get("should_end", False),
            "collected_info": {
                "age": result.get("age", ""),
                "gender": result.get("gender", ""),
                "body_region": result.get("body_region", ""),
                "symptoms": result.get("symptoms", {}),
                "skin_cancer_history": result.get("skin_cancer_history", ""),
                "family_cancer_history": result.get("family_cancer_history", ""),
                "duration": result.get("duration", ""),
                "other_information": result.get("other_information", "")
            },
            "api_calls": 1  # Always 1 call per message now!
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/state/<thread_id>", methods=["GET"])
def get_state(thread_id):
    """
    Get current state of a consultation
    
    Returns the full state including chat_history and collected information
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            state = workflow.get_state(config).values
            
            return jsonify({
                "status": "success",
                "thread_id": thread_id,
                "chat_history": state.get("chat_history", []),
                "information_complete": state.get("information_complete", False),
                "should_request_image": state.get("should_end", False),
                "collected_info": {
                    "age": state.get("age", ""),
                    "gender": state.get("gender", ""),
                    "body_region": state.get("body_region", ""),
                    "symptoms": state.get("symptoms", {}),
                    "skin_cancer_history": state.get("skin_cancer_history", ""),
                    "family_cancer_history": state.get("family_cancer_history", ""),
                    "duration": state.get("duration", ""),
                    "other_information": state.get("other_information", "")
                },
                "message_count": len(state.get("chat_history", []))
            })
        except:
            return jsonify({
                "status": "error",
                "error": f"No consultation found with thread_id: {thread_id}"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# =============================================================================
# START FLASK APP
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Skin Specialist Agent (Optimized) on port {port}")
    print(f"🏥 Project: {PROJECT_ID}")
    print(f"📍 Location: {LOCATION}")
    print(f"⚡ Optimization: Single API call per message")
    app.run(host="0.0.0.0", port=port, debug=False)