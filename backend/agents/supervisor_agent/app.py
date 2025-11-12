# =============================================================================
# FILE: app.py - FastAPI Supervisor Agent (Production Ready)
# =============================================================================

from dotenv import load_dotenv
load_dotenv()

import os, asyncio
import httpx
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

# internal imports
from security_guardrails import SecurityOrchestrator
from firestore_service import FirestoreService
from utils.validators import validate_image_url
from utils.http_client import HttpClient


# ---------------------------------------------------------------------
# ENV
# ---------------------------------------------------------------------
PORT = int(os.getenv("PORT", "8080"))
ENABLE_SECURITY = os.getenv("ENABLE_SECURITY", "true").lower() == "true"

SKIN_AGENT_URL      = os.getenv("SKIN_AGENT_URL", "")
ORAL_AGENT_URL      = os.getenv("ORAL_AGENT_URL", "")
VISION_AGENT_URL    = os.getenv("VISION_AGENT_URL", "")
REPORTING_AGENT_URL = os.getenv("REPORTING_AGENT_URL", "")

REQUIRED = [SKIN_AGENT_URL, ORAL_AGENT_URL, VISION_AGENT_URL, REPORTING_AGENT_URL]
if not all(REQUIRED):
    raise RuntimeError("Missing one or more agent URLs in environment variables")


# ---------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------
class MessageTurn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str

class SupervisorRequest(BaseModel):
    message: Optional[str] = None
    image_url: Optional[str] = None
    user: Optional[str] = None
    user_id: str
    chat_id: str
    type: str = Field(..., pattern="^(text|image)$")
    speciality: str = Field(..., pattern="^(skin|oral)$")
    history: List[MessageTurn] = Field(default_factory=list)

class AgentResponse(BaseModel):
    success: bool
    response: str
    response_type: str
    chat_id: str
    metadata: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def ok(chat_id: str, msg: str, typ: str, meta: Dict[str, Any]) -> AgentResponse:
    return AgentResponse(success=True, response=msg, response_type=typ, chat_id=chat_id, metadata=meta)

def err(chat_id: str, msg: str, typ: str, meta: Optional[Dict[str, Any]] = None) -> AgentResponse:
    return AgentResponse(
        success=False,
        response=msg,
        response_type="error",
        chat_id=chat_id,
        metadata=meta or {"error_type": typ},
        error={"type": typ, "message": msg},
    )

def validate_payload(req: SupervisorRequest):
    """Validate the input payload and perform basic image URL checks."""
    if req.type == "text" and not req.message:
        raise HTTPException(400, "message required for type='text'")
    if req.type == "image":
        # Only validate URL format - let Vision Agent handle image content validation
        ok_url, msg = validate_image_url(req.image_url or "")
        if not ok_url:
            raise HTTPException(400, msg)


# ---------------------------------------------------------------------
# CORE APP
# ---------------------------------------------------------------------
app = FastAPI(title="Supervisor Agent", version="3.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

guardrails = SecurityOrchestrator(enabled=ENABLE_SECURITY)
http = HttpClient(timeout=25, retries=2)
db = FirestoreService()


@app.get("/health")
async def health(): return {"status": "ok"}

@app.get("/ready")
async def ready(): return {"status": "ready"}


# ---------------------------------------------------------------------
# INTERNAL LOGGING TASKS
# ---------------------------------------------------------------------
async def _log_user_message(req: SupervisorRequest):
    doc = {
        "sender": "user",
        "user": req.user or "",
        "userId": req.user_id,
        "createdAt": datetime.utcnow(),
        "text": req.message if req.type == "text" else "[Image sent]",
    }
    if req.type == "image":
        doc["image"] = req.image_url
    db.save_message(req.chat_id, doc)

async def _log_bot_message(req: SupervisorRequest, response: AgentResponse):
    bot_doc = {
        "sender": "bot",
        "user": "AI Bot",
        "userId": req.user_id,
        "text": response.response,
        "createdAt": datetime.utcnow(),
    }
    db.save_message(req.chat_id, bot_doc)


# ---------------------------------------------------------------------
# AGENT ROUTING
# ---------------------------------------------------------------------
async def _route_text(req: SupervisorRequest) -> AgentResponse:
    """
    Route text messages from the Supervisor Agent to Skin/Oral Agents.
    Ensures payload matches the expected format of the downstream /chat API.
    """
    print("🔍 Request:", req, flush=True)
    agent_url = (
        SKIN_AGENT_URL if req.speciality == "skin" else ORAL_AGENT_URL
    )
    # 🧩 Build chat history cleanly for multi-turn flow
    chat_history = [ {"role": h.role, "content": h.content} for h in req.history ]

    # Only append current message if it's not already the last message in history
    # (prevents duplication since the agent will also add it)
    last_message_in_history = chat_history[-1] if chat_history else None
    if not last_message_in_history or last_message_in_history.get("content") != req.message:
        chat_history.append({"role": "user", "content": req.message})
    
    print("🧾 Full chat history being sent:", chat_history, flush=True)
    payload = {"thread_id": req.chat_id, "message": req.message, "chat_history": chat_history}

    print("➡️ Sending to Agent:", agent_url)
    print("🧾 Payload:", payload)

    try:
        # Post JSON (httpx must use json=data)
        data = await http.post_json(agent_url, payload)
        # print("🔍 Agent response:", data)
        if req.message:
            req.history.append(MessageTurn(role="user", content=req.message))

        if data.get("response"):
            # print("🔍 Adding assistant response to history:", data["response"])
            req.history.append(MessageTurn(role="assistant", content=data["response"]))
            # print("🔍 History after adding assistant response:", req.history)
        else:
            print("❌ No response from agent")

                # ✅ Expected fields from agent response
        msg = data.get("response", "")
        should_request_image = data.get("should_request_image", False)
        collected_info = data.get("collected_info", {})
        
        # Save collected_info to Firestore chat document for later use
        if collected_info:
            try:
                db.db.collection("chats").document(req.chat_id).set(
                    {"user_metadata": collected_info},
                    merge=True  # Merge with existing data, latest values overwrite
                )
                print(f"✅ Saved collected_info to Firestore: {collected_info}")
            except Exception as e:
                print(f"⚠️  Could not save collected_info to Firestore: {e}")
        
        meta = {
            "thread_id": data.get("thread_id"),
            "chat_history": data.get("chat_history", []),
            "information_complete": data.get("information_complete", False),
            "should_request_image": should_request_image,
            "ready_for_images": should_request_image,
            "collected_info": collected_info,
            "api_calls": data.get("api_calls", 1),
        }

        return ok(req.chat_id, msg, "text", meta)

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Downstream {agent_url} error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Downstream {agent_url} error: {e}")


async def _route_image_then_report(req: SupervisorRequest) -> AgentResponse:
    """Send image to Vision Agent, then Reporting Agent."""
    
    # Vision Agent - send with image_url
    vision_payload = {
        "image_url": req.image_url,
        "user_id": req.user_id,
        "chat_id": req.chat_id,
        "chat_type": req.speciality,
        "message_type": "image",
    }
    print("🔍 Vision payload:", vision_payload, flush=True)
    vision = await http.post_json(VISION_AGENT_URL, vision_payload)
    print("🔍 Vision response:", vision, flush=True)
    
    # Check if image is valid
    is_valid = vision.get("is_valid", False)
    validation_reason = vision.get("validation_reason", "")
    
    if not is_valid:
        # Image is invalid - return error to user
        error_msg = f"Invalid image: {validation_reason}"
        response = err(
            req.chat_id,
            error_msg,
            "invalid_image",
            {
                "validation_reason": validation_reason,
                "error_type": "image_validation_failed"
            }
        )
        await _log_bot_message(req, response)
        return response
    
    # Image is valid - extract prediction result
    prediction_result = vision.get("prediction_result")
    if not prediction_result:
        raise HTTPException(502, "Vision agent returned valid image but no prediction result")
    
    # Extract diagnosis from prediction_result
    # prediction_result has: {"confidence": float, "predicted_class": str}
    diagnosis = {
        "diagnosis_name": prediction_result.get("predicted_class", "Unknown"),
        "confidence": prediction_result.get("confidence", 0.0),
    }

    db.log_vision_result(req.chat_id, {
        "speciality": req.speciality,
        "diagnosis": diagnosis["diagnosis_name"],
        "confidence": diagnosis["confidence"],
    })
    
        # Get collected_info from Firestore (saved during text conversations)
    collected_info = {}
    try:
        chat_doc_ref = db.db.collection("chats").document(req.chat_id)
        chat_doc = chat_doc_ref.get()
        if chat_doc.exists:
            chat_data = chat_doc.to_dict()
            collected_info = chat_data.get("user_metadata", {})
            print(f"✅ Retrieved user_metadata from Firestore: {collected_info}")
        else:
            print("⚠️  Chat document not found in Firestore, user_metadata will be empty")
    except Exception as e:
        print(f"⚠️  Could not fetch user_metadata from Firestore: {e}")

    # Reporting Agent
    report_payload = {
        "user_id": req.user_id,
        "chat_id": req.chat_id,
        "speciality": req.speciality,
        "type": "report",
        "history": [h.model_dump() for h in req.history],
        "diagnosis": diagnosis,
        "image_url": req.image_url,
        "metadata": collected_info,
    }
    
    print("🔍 Report payload:", report_payload, flush=True)
    
    report = await http.post_json(REPORTING_AGENT_URL, report_payload)
    print("🔍 Report response received:", report, flush=True)

    # Extract the report field directly - it contains all the key values
    report_data = report.get("report", {})
    diagnosis_from_report = report.get("diagnosis", diagnosis)  # Use report's diagnosis if available
    
    # Extract the main output message (this is the user-friendly message from the report)
    report_output = report_data.get("output") or "Your report is ready."
    
    # Build metadata with the complete report structure
    meta = {
        "diagnosis": diagnosis_from_report,
        "report": report_data,  # Return the entire report object as-is
        "image_description": report.get("image_description"),
        "image_url": report.get("image_url", req.image_url),
        "speciality": report.get("speciality", req.speciality),
        "generated_at": report.get("generated_at"),
        "status": report.get("status", "success"),
        "message_state": "COMPLETED",
        "ready_for_images": False,
        "validation_reason": validation_reason,
    }
    
    # Use the output field as the main response message
    final = ok(req.chat_id, report_output, "report", meta)
    
    # Save full report to Firestore
    db.save_report(req.chat_id, {
        "diagnosis": diagnosis_from_report, 
        "report": report_data,  # Save the complete report structure
        "full_report_response": report  # Optionally save the entire response for debugging
    })
    
    return final


# ---------------------------------------------------------------------
# MAIN ENTRY
# ---------------------------------------------------------------------
@app.post("/api/v1/main", response_model=AgentResponse)
async def main_entry(payload: Dict[str, Any]):
    try:
        req = SupervisorRequest(**payload)
    except ValidationError as e:
        raise HTTPException(400, f"Invalid payload: {e}")

    validate_payload(req)
    await _log_user_message(req)

    # security guardrails - pass history for context-aware domain grounding
    if req.type == "text":
        # Convert history to format expected by security guardrails
        history_for_validation = [{"role": h.role, "content": h.content} for h in req.history] if req.history else []
        ok_sec, msg, meta = guardrails.validate_input(
            req.user_id, 
            req.message or "", 
            req.type, 
            req.speciality,
            history=history_for_validation
        )
        if not ok_sec:
            response = err(req.chat_id, msg, meta.get("error_type", "security"), meta)
            await _log_bot_message(req, response)
            return response

    # route message/image
    try:
        response = await (_route_text(req) if req.type == "text" else _route_image_then_report(req))
        await _log_bot_message(req, response)
        return response
    except HTTPException:
        raise
    except Exception as e:
        response = err(req.chat_id, "Internal server error", "internal_error", {"detail": str(e)})
        await _log_bot_message(req, response)
        return response


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, log_level="info")