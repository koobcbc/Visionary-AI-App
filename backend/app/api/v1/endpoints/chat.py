"""
Chat endpoints for healthcare diagnostic API
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import requests
import base64
from datetime import datetime

from app.api.v1.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    MessageType,
    ResponseStatus
)
from app.core.dependencies import get_current_user, rate_limiter_standard
from app.core.exceptions import SessionExpiredError, ValidationError
from app.services.llm.gemini_service import GeminiService
from app.services.cv.cv_model_service import CVModelService
from app.services.storage.firestore_service import FirestoreService
from app.models.enums import HealthSpeciality
from app.core.logging import log_api_request, log_api_response, log_error, logger

router = APIRouter()


@router.post("/process", response_model=ChatResponse)
async def call_main_api(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limit: bool = Depends(rate_limiter_standard),
    firestore_service: FirestoreService = Depends()
):
    """
    Main API endpoint - call_main_api
    
    Parameters:
    - message: empty or string
    - image_url: empty or string  
    - user_id: string
    - chat_id: string
    - type: "text" or "image"
    - speciality: "dental" or "skin"
    
    Output:
    - response: string (markdown format)
    - status: "response", "warning", "report"
    """
    try:
        log_api_request(
            method="POST",
            path="/chat/process",
            user_id=current_user["user_id"],
            request_id=request.chat_id
        )
        
        # Get or create chat session with metadata caching
        chat_data = await firestore_service.get_or_create_chat(
            chat_id=request.chat_id,
            user_id=current_user["user_id"],
            speciality=request.speciality.value
        )
        
        # Check session expiry (2hrs limit as specified)
        if firestore_service.is_session_expired(chat_data):
            raise SessionExpiredError()
        
        # Initialize services
        llm_service = GeminiService()
        
        # Process based on message type
        if request.type == MessageType.TEXT:
            result = await _process_text_message(
                request, chat_data, llm_service, firestore_service
            )
        else:
            result = await _process_image_message(
                request, chat_data, llm_service, firestore_service, background_tasks
            )
        
        log_api_response(
            method="POST",
            path="/chat/process",
            status_code=200,
            response_time_ms=0,  # Would be calculated in middleware
            user_id=current_user["user_id"],
            request_id=request.chat_id
        )
        
        return result
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"], request_id=request.chat_id)
        raise


@router.get("/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    chat_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    firestore_service: FirestoreService = Depends()
):
    """
    Get chat history for a specific chat session
    """
    try:
        log_api_request(
            method="GET",
            path=f"/chat/{chat_id}",
            user_id=current_user["user_id"]
        )
        
        chat_data = await firestore_service.get_chat_by_id(
            chat_id=chat_id,
            user_id=current_user["user_id"]
        )
        
        if not chat_data:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return ChatHistoryResponse(
            chat_id=chat_id,
            messages=chat_data.get("messages", []),
            metadata=chat_data.get("metadata", {}),
            status="active" if not chat_data.get("image_analyzed") else "completed"
        )
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"])
        raise


@router.delete("/{chat_id}")
async def delete_chat_session(
    chat_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    firestore_service: FirestoreService = Depends()
):
    """
    Delete a chat session
    """
    try:
        log_api_request(
            method="DELETE",
            path=f"/chat/{chat_id}",
            user_id=current_user["user_id"]
        )
        
        success = await firestore_service.delete_chat(
            chat_id=chat_id,
            user_id=current_user["user_id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {"message": "Chat session deleted successfully"}
        
    except Exception as e:
        log_error(e, user_id=current_user["user_id"])
        raise


async def _process_text_message(
    request: ChatRequest,
    chat_data: Dict[str, Any],
    llm_service: GeminiService,
    firestore_service: FirestoreService
) -> ChatResponse:
    """Process text message"""
    
    # Add user message to history
    await firestore_service.add_message(
        chat_id=request.chat_id,
        role="patient",
        content=request.message,
        metadata={"type": "text"}
    )
    
    # First, try to extract metadata from the user's message
    logger.info(f"🔍 Attempting to extract metadata from: '{request.message}'")
    extracted_metadata = await _extract_metadata_from_message(
        request.message, request.speciality, llm_service
    )
    logger.info(f"📋 Extracted metadata result: {extracted_metadata}")
    
    # Update metadata if we found any
    if extracted_metadata:
        current_metadata = chat_data.get("metadata", {})
        current_metadata.update(extracted_metadata)
        logger.info(f"💾 Updating metadata with: {current_metadata}")
        await firestore_service.update_metadata(
            chat_id=request.chat_id,
            metadata=current_metadata
        )
        # Refresh chat_data with updated metadata
        chat_data = await firestore_service.get_or_create_chat(
            chat_id=request.chat_id,
            user_id=request.user_id,
            speciality=request.speciality.value
        )
        logger.info(f"🔄 Refreshed chat_data metadata: {chat_data.get('metadata', {})}")
    else:
        logger.warning("⚠️ No metadata extracted from user message")
    
    # Check if essential metadata is missing
    current_metadata = chat_data.get("metadata", {})
    missing_metadata = _check_missing_metadata(current_metadata, request.speciality)
    
    # Determine the conversation flow stage
    conversation_stage = _determine_conversation_stage(current_metadata, missing_metadata, request.speciality)
    
    if conversation_stage == "collect_metadata":
        # Stage 1: Collect essential metadata
        metadata_request_message = await _generate_dynamic_metadata_request(
            missing_metadata, request.speciality, chat_data, llm_service
        )
        
        # Add AI response asking for metadata
        await firestore_service.add_message(
            chat_id=request.chat_id,
            role="assistant",
            content=metadata_request_message,
            metadata={"type": "metadata_request"}
        )
        
        return ChatResponse(
            response=metadata_request_message,
            status=ResponseStatus.RESPONSE,
            metadata={
                "missing_metadata": missing_metadata,
                "should_upload_image": False,
                "conversation_stage": "collect_metadata"
            }
        )
    
    elif conversation_stage == "request_image":
        # Stage 2: Request image for analysis
        image_request_message = await _generate_image_request_message(
            request.speciality, chat_data, llm_service
        )
        
        # Add AI response asking for image
        await firestore_service.add_message(
            chat_id=request.chat_id,
            role="assistant",
            content=image_request_message,
            metadata={"type": "image_request"}
        )
        
        return ChatResponse(
            response=image_request_message,
            status=ResponseStatus.WARNING,  # Warning status to indicate image upload needed
            metadata={
                "should_upload_image": True,
                "conversation_stage": "request_image"
            }
        )
    
    elif conversation_stage == "continue_questions":
        # Stage 3: Continue asking questions if no image provided
        followup_message = await _generate_followup_questions(
            request.speciality, chat_data, llm_service
        )
        
        # Add AI response with followup questions
        await firestore_service.add_message(
            chat_id=request.chat_id,
            role="assistant",
            content=followup_message,
            metadata={"type": "followup_questions"}
        )
        
        return ChatResponse(
            response=followup_message,
            status=ResponseStatus.RESPONSE,
            metadata={
                "should_upload_image": False,
                "conversation_stage": "continue_questions"
            }
        )
    
    # Get AI response with context
    result = await llm_service.chat_with_context(
        chat_data=chat_data,
        user_message=request.message
    )
    
    # Update metadata if extracted
    if result.get("extracted_metadata"):
        current_metadata = chat_data.get("metadata", {})
        current_metadata.update(result["extracted_metadata"])
        await firestore_service.update_metadata(
            chat_id=request.chat_id,
            metadata=current_metadata
        )
    
    # Add AI response to history
    await firestore_service.add_message(
        chat_id=request.chat_id,
        role="assistant",
        content=result["response"],
        metadata={"type": "ai_response"}
    )
    
    # Determine status
    status = ResponseStatus.WARNING if "upload" in result["response"].lower() else ResponseStatus.RESPONSE
    
    return ChatResponse(
        response=result["response"],
        status=status,
        metadata={
            "should_upload_image": result.get("should_request_image", False)
        }
    )


async def _process_image_message(
    request: ChatRequest,
    chat_data: Dict[str, Any],
    llm_service: GeminiService,
    firestore_service: FirestoreService,
    background_tasks: BackgroundTasks
) -> ChatResponse:
    """Process image message and generate final report"""
    
    # Download/decode image
    if request.image_url.startswith("http"):
        response = requests.get(request.image_url)
        image_data = response.content
    else:
        # Assume base64
        image_data = base64.b64decode(request.image_url)
    
    # Validate image with Gemini (using your notebook approach)
    is_valid, reason = await llm_service.validate_image_content(
        image_data=image_data,
        speciality=request.speciality.value
    )
    
    if not is_valid:
        return ChatResponse(
            response=f"⚠️ **Image Validation Failed**\n\n{reason}\n\nPlease upload a clear photo of the affected area.",
            status=ResponseStatus.WARNING
        )
    
    # Call CV model with validation and fallback
    cv_service = CVModelService()
    try:
        if request.speciality == HealthSpeciality.SKIN:
            cv_result = await cv_service.analyze_skin_image(image_data)
        else:
            cv_result = await cv_service.analyze_oral_image(image_data)
        
        logger.info(f"✅ CV analysis completed: {cv_result.get('predicted_class', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"❌ CV analysis failed: {e}")
        # The CV service now has built-in fallback, so this shouldn't happen
        # But just in case, create a minimal fallback result
        cv_result = {
            "predicted_class": "Analysis Failed",
            "confidence": 0.0,
            "disease_type": "Unable to Analyze",
            "severity": "Unknown",
            "description": "Unable to analyze the image due to technical issues.",
            "recommendations": ["Consult a healthcare professional for proper evaluation"],
            "model_version": "fallback-1.0",
            "analysis_timestamp": datetime.now().isoformat(),
            "cv_model_unavailable": True,
            "error_message": str(e)
        }
    
    # Save CV result
    await firestore_service.save_cv_result(request.chat_id, cv_result)
    
    # Generate final report using your exact prompt engineering approach
    report = await llm_service.generate_final_report(chat_data, cv_result, image_data)
    
    # Save report
    await firestore_service.save_report(request.chat_id, request.user_id, report)
    
    # Clear cache for this session (metadata cached until final report)
    firestore_service.clear_cache(request.chat_id)
    
    return ChatResponse(
        response=report.get("output", "Report generated successfully"),
        status=ResponseStatus.REPORT,  # Final report status as specified
        metadata=report
    )


def _determine_conversation_stage(metadata: Dict[str, Any], missing_metadata: List[str], speciality: HealthSpeciality) -> str:
    """Determine the current stage of the conversation flow"""
    
    # Essential metadata for both specialties
    essential_fields = ["age", "gender", "medical_history"]
    
    # Check if we have essential metadata
    has_essential_metadata = all(metadata.get(field) for field in essential_fields)
    
    if not has_essential_metadata:
        return "collect_metadata"
    
    # Check if we have specialty-specific metadata
    if speciality == HealthSpeciality.SKIN:
        specialty_fields = ["skin_type", "sun_exposure"]
    else:  # DENTAL
        specialty_fields = ["dental_history", "oral_hygiene"]
    
    has_specialty_metadata = all(metadata.get(field) for field in specialty_fields)
    
    if not has_specialty_metadata:
        return "collect_metadata"
    
    # Check if we've already requested an image recently
    # This would need to be tracked in the conversation history
    # For now, we'll assume if we have enough metadata, we can request image
    return "request_image"


async def _generate_image_request_message(
    speciality: HealthSpeciality, 
    chat_data: Dict[str, Any], 
    llm_service: GeminiService
) -> str:
    """Generate a message requesting image upload"""
    
    current_metadata = chat_data.get("metadata", {})
    conversation_history = chat_data.get("messages", [])
    
    context_prompt = f"""
You are a compassionate healthcare assistant specializing in {speciality.value} health.

**Patient's Information:**
{_format_current_metadata(current_metadata)}

**Recent Conversation:**
{_format_conversation_history(conversation_history[-3:])}

**Your Task:**
Generate a warm, encouraging message asking the patient to upload an image for analysis. Make it:

1. **Acknowledging**: Reference the information they've shared
2. **Encouraging**: Make them feel comfortable about sharing images
3. **Clear**: Explain why the image is important
4. **Reassuring**: Address any privacy concerns
5. **Specific**: Mention what type of image you need

**Guidelines:**
- Use supportive, professional language
- Explain the benefits of image analysis
- Keep it concise (2-3 sentences)
- Make them feel confident about the process

**Example Style:**
"Thank you for sharing your information. To provide you with the most accurate {speciality.value} assessment, I'd like to analyze an image of the area you're concerned about. This will help me give you a more detailed evaluation and recommendations."

Generate a personalized, encouraging image request message.
"""
    
    try:
        response = await llm_service.generate_metadata_request(context_prompt)
        return response
    except Exception as e:
        logger.error(f"Error generating image request: {e}")
        return f"Thank you for sharing your information. To provide you with the most accurate {speciality.value} assessment, I'd like to analyze an image of the area you're concerned about."


async def _generate_followup_questions(
    speciality: HealthSpeciality, 
    chat_data: Dict[str, Any], 
    llm_service: GeminiService
) -> str:
    """Generate followup questions when no image is provided"""
    
    current_metadata = chat_data.get("metadata", {})
    conversation_history = chat_data.get("messages", [])
    
    context_prompt = f"""
You are a compassionate healthcare assistant specializing in {speciality.value} health.

**Patient's Information:**
{_format_current_metadata(current_metadata)}

**Recent Conversation:**
{_format_conversation_history(conversation_history[-3:])}

**Your Task:**
Generate followup questions to gather more information since no image was provided. Make it:

1. **Understanding**: Acknowledge they may not have an image ready
2. **Helpful**: Ask questions that will help with assessment
3. **Encouraging**: Keep them engaged in the conversation
4. **Specific**: Ask about symptoms, duration, severity, etc.
5. **Reassuring**: Let them know you can still help

**Guidelines:**
- Ask 1-2 specific, relevant questions
- Use conversational, supportive language
- Focus on symptoms and concerns
- Keep it concise (2-3 sentences)

**Example Style:**
"I understand you may not have an image ready. Could you tell me more about your symptoms - when did you first notice this, and has it changed over time?"

Generate helpful followup questions.
"""
    
    try:
        response = await llm_service.generate_metadata_request(context_prompt)
        return response
    except Exception as e:
        logger.error(f"Error generating followup questions: {e}")
        return f"I understand you may not have an image ready. Could you tell me more about your {speciality.value} concerns and symptoms?"


def _check_missing_metadata(metadata: Dict[str, Any], speciality: HealthSpeciality) -> List[str]:
    """Check what essential metadata is missing"""
    essential_fields = ["age", "gender", "medical_history"]
    
    # Add speciality-specific fields
    if speciality == HealthSpeciality.SKIN:
        essential_fields.extend(["skin_type", "sun_exposure", "family_history"])
    elif speciality == HealthSpeciality.DENTAL:
        essential_fields.extend(["dental_history", "oral_hygiene", "smoking_status"])
    
    missing_fields = []
    for field in essential_fields:
        if not metadata.get(field):
            missing_fields.append(field)
    
    return missing_fields


async def _generate_dynamic_metadata_request(
    missing_fields: List[str], 
    speciality: HealthSpeciality, 
    chat_data: Dict[str, Any],
    llm_service: GeminiService
) -> str:
    """Generate a dynamic, contextual metadata request using Gemini"""
    
    # Get conversation history for context
    conversation_history = chat_data.get("messages", [])
    current_metadata = chat_data.get("metadata", {})
    
    # Create context for Gemini
    context_prompt = f"""
You are a compassionate healthcare assistant specializing in {speciality.value} health. 

**Patient's Current Information:**
{_format_current_metadata(current_metadata)}

**Missing Information Needed:**
{', '.join(missing_fields)}

**Recent Conversation Context:**
{_format_conversation_history(conversation_history[-3:])}  # Last 3 messages for context

**Your Task:**
Generate a warm, empathetic response asking for the missing information. Make it:

1. **Personal & Acknowledging**: Reference what they've already shared
2. **Empathetic**: Show understanding of their concern
3. **Contextual**: Ask questions relevant to their specific {speciality.value} issue
4. **Non-repetitive**: Don't ask for information they've already provided
5. **Encouraging**: Make them feel comfortable sharing
6. **Specific**: Ask for the most important missing information first

**Guidelines:**
- Use "I understand" or "I appreciate you sharing" to acknowledge their input
- Ask 1-2 most critical questions, not all at once
- Use conversational, supportive language
- Avoid medical jargon
- Keep it concise (2-3 sentences)

**Example Style:**
"I appreciate you sharing your age and gender. To give you the most accurate skin assessment, I'd like to know about any allergies or medical conditions you have, as these can affect skin health."

Generate a warm, personalized response.
"""
    
    try:
        logger.info(f"🤖 Generating dynamic metadata request for missing fields: {missing_fields}")
        logger.info(f"📝 Current metadata: {current_metadata}")
        logger.info(f"💬 Recent conversation: {conversation_history[-3:]}")
        
        # Use Gemini to generate the response
        response = await llm_service.generate_metadata_request(context_prompt)
        logger.info(f"🤖 Generated dynamic response: {response}")
        return response
    except Exception as e:
        logger.error(f"❌ Error generating dynamic metadata request: {e}")
        # Generate a simple dynamic response without static fallback
        return f"I'd like to learn more about your {speciality.value} health. Could you tell me about your {missing_fields[0].replace('_', ' ')}?"


def _format_current_metadata(metadata: Dict[str, Any]) -> str:
    """Format current metadata for context"""
    if not metadata:
        return "No information provided yet."
    
    formatted = []
    for key, value in metadata.items():
        if value:
            formatted.append(f"{key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(formatted) if formatted else "No information provided yet."


def _format_conversation_history(messages: List[Dict[str, Any]]) -> str:
    """Format conversation history for context"""
    if not messages:
        return "No previous conversation."
    
    formatted = []
    for msg in messages:
        role = "Patient" if msg.get("role") == "patient" else "Assistant"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted)




async def _extract_metadata_from_message(
    message: str, 
    speciality: HealthSpeciality, 
    llm_service: GeminiService
) -> Dict[str, Any]:
    """Extract metadata from user message using Gemini's natural language understanding"""
    
    extraction_prompt = f"""
You are a medical assistant specializing in {speciality.value} health. Analyze this patient message and extract relevant medical information.

Patient message: "{message}"

Using your natural language understanding, identify and extract ONLY the information that is clearly stated or strongly implied:

**Basic Demographics:**
- age: Extract numeric age (e.g., "25 years old" → 25, "in my thirties" → 30)
- gender: Extract gender identity (e.g., "female" → "female", "I'm a woman" → "female", "male" → "male")

**Medical Information:**
- medical_history: Any mentioned medical conditions, allergies, medications, chronic diseases
- family_history: Family medical history, genetic conditions, hereditary diseases

**Specialty-Specific Information:**
{f"- skin_type: Skin characteristics (oily, dry, combination, sensitive, normal)" if speciality == HealthSpeciality.SKIN else ""}
{f"- sun_exposure: Sun exposure patterns (minimal, moderate, high, daily, occasional)" if speciality == HealthSpeciality.SKIN else ""}
{f"- dental_history: Previous dental treatments, procedures, issues" if speciality == HealthSpeciality.DENTAL else ""}
{f"- oral_hygiene: Brushing/flossing habits, dental care routine" if speciality == HealthSpeciality.DENTAL else ""}
{f"- smoking_status: Smoking, vaping, tobacco use (current, former, never)" if speciality == HealthSpeciality.DENTAL else ""}

**CRITICAL INSTRUCTIONS:**
1. Be VERY precise - only extract information that is explicitly stated
2. For gender: "female" = "female", "woman" = "female", "male" = "male", "man" = "male"
3. For age: Extract exact numbers, convert ranges to specific values
4. If information is not clearly stated, DO NOT include it
5. Return ONLY a valid JSON object with extracted fields
6. If no information is found, return {{}}

**Examples:**
- "I am 25 years old female" → {{"age": 25, "gender": "female"}}
- "I'm a woman in my thirties" → {{"age": 30, "gender": "female"}}
- "I have sensitive skin" → {{"skin_type": "sensitive"}}
- "I work outdoors daily" → {{"sun_exposure": "high"}}

Extract information precisely and conservatively.
"""
    
    try:
        logger.info(f"🤖 Sending extraction prompt to Gemini...")
        response = await llm_service.extract_metadata(extraction_prompt)
        logger.info(f"🤖 Raw Gemini response: {response}")
        
        # Parse JSON response
        import json
        try:
            metadata = json.loads(response)
            logger.info(f"✅ Successfully parsed metadata: {metadata}")
            return metadata
        except json.JSONDecodeError as e:
            logger.warning(f"❌ Failed to parse metadata JSON: {e}")
            logger.warning(f"Raw response was: {response}")
            # Try to extract JSON from response if it's wrapped in text
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    metadata = json.loads(json_match.group())
                    logger.info(f"✅ Extracted JSON from wrapped response: {metadata}")
                    return metadata
                else:
                    logger.warning("No JSON pattern found in response")
            except Exception as extract_error:
                logger.error(f"Error extracting JSON: {extract_error}")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Error extracting metadata: {e}")
        return {}
