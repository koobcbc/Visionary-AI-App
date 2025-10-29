"""
Gemini LLM service with LangChain caching
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from google import genai
from google.genai import types
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache

from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.core.logging import logger
from app.models.enums import ResponseStatus


class GeminiService:
    """Handles all LLM interactions with caching"""
    
    def __init__(self):
        # Setup LangChain caching
        set_llm_cache(InMemoryCache())
        
        self.client = genai.Client(
            vertexai=True,
            project=settings.GCP_PROJECT_ID,
            location="us-central1"
        )
    
    async def chat_with_context(self, chat_data: Dict[str, Any], user_message: str) -> Dict[str, Any]:
        """Generate response with full context (matching your notebook approach)"""
        try:
            speciality = chat_data.get("speciality", "skin")
            messages = chat_data.get("messages", [])
            metadata = chat_data.get("metadata", {})
            
            # Build conversation history (matching your notebook approach)
            history = []
            
            # Add system instructions embedded as the first user message (from your notebook)
            system_prompt = (
                "You are a helpful Dermatology AI assistant. Ask the user for information like Age, Gender, "
                "Skin cancer history, any cancer history, the body region where they see something suspicious, "
                "and symptoms (Does it itch, hurt, grow, change, or bleed?). "
                "Stop asking further questions once the user has provided all necessary information. Once you have enough information ask to upload the image of the part of the body."
            )
            
            history.append(types.Content(
                role="user",
                parts=[types.Part(text=system_prompt)]
            ))
            
            # Add conversation history
            for msg in messages[-20:]:  # Last 20 messages for context
                role = "user" if msg["role"] == "patient" else "model"
                history.append(types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])]
                ))
            
            # Add current message
            history.append(types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            ))
            
            # Optional tools config (matching your notebook)
            config = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=history,
                config=config
            )
            
            ai_response = response.candidates[0].content.parts[0].text
            
            # Extract metadata if present
            extracted_metadata = self._extract_metadata(user_message, ai_response)
            
            # Determine if we should request image
            should_request_image = self._should_request_image(messages, metadata)
            
            return {
                "response": ai_response,
                "status": ResponseStatus.RESPONSE,
                "extracted_metadata": extracted_metadata,
                "should_request_image": should_request_image
            }
            
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise LLMServiceError(f"AI processing error: {str(e)}")
    
    async def generate_final_report(
        self, 
        chat_data: Dict[str, Any], 
        cv_result: Dict[str, Any], 
        image_data: bytes
    ) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report using your exact prompt engineering approach"""
        try:
            speciality = chat_data.get("speciality")
            metadata = chat_data.get("metadata", {})
            messages = chat_data.get("messages", [])
            
            # Build chat history for context (matching your notebook approach)
            chat_history = []
            for msg in messages[-10:]:  # Last 10 messages
                role = "user" if msg["role"] == "patient" else "model"
                chat_history.append(f"{role}: {msg['content']}")
            
            # Use your exact prompt from the notebook
            prompt = f"""
You are a dermatology AI assistant. Use the following data:
1. Chat history: {chat_history}
2. Computer vision model output: {json.dumps(cv_result)}
3. Uploaded skin image.

Generate a structured JSON output with ONLY these fields:

{{
  "disease_type": "<Predicted disease or condition>",
  "disease_meaning_plain_english": "<Simple explanation of what it means>",
  "follow_up_required": "<Yes or No>",
  "home_remedy_enough": "<Yes or No>",
  "home_remedy_details": "<If Yes, describe safe remedies briefly>",
  "age": "<Extracted from user's chat history>",
  "gender": "<Extracted from user's chat history>",
  "symptoms": "<List key symptoms user mentioned>",
  "other_information": "<Any other context the user shared>",
  "output": "<Single plain-English message for the user combining all the above info in clear, empathetic language. Do not mention confidence here.>"
}}

Rules:
- Return ONLY valid JSON — no extra text or commentary.
- The 'output' field should summarize the key points clearly and concisely for the user.
- Use plain English and an empathetic tone.
- If confidence is low or disease uncertain, mark "follow_up_required": "Yes".
- If no home remedies are safe, set "home_remedy_enough": "No".
"""
            
            # Build contents array with chat history and image (matching your notebook)
            contents = []
            
            # Add system prompt as first user message
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            ))
            
            # Add image
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_bytes(data=image_data, mime_type="image/png")]
            ))
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=[types.Modality.TEXT],
                    candidate_count=1
                )
            )
            
            result_text = response.candidates[0].content.parts[0].text
            # Clean up the response (remove markdown code blocks if present)
            cleaned_text = result_text.strip('```json').strip('```').strip()
            report = json.loads(cleaned_text)
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            raise LLMServiceError(f"Report generation failed: {str(e)}")
    
    async def validate_image_content(self, image_data: bytes, speciality: str) -> tuple[bool, str]:
        """Use Gemini to validate if image is relevant (matching your notebook approach)"""
        try:
            prompt = f"""You are a dermatology AI assistant. Analyze the uploaded image and determine if it is relevant for skin cancer analysis. \
            - If the image shows skin lesions suitable for analysis, output a JSON: {{"valid": "Yes"}}. \
            - If the image is not relevant (e.g., normal objects, unrelated skin, or non-skin content), output a JSON: {{"valid": "No", "reason": "<explain why the image is invalid>"}}. \
            Return only valid JSON, no extra text."""
            
            # Prepare contents: wrap image and prompt in Content + Part (matching your notebook)
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                ),
                types.Content(
                    role="user",
                    parts=[types.Part.from_bytes(
                        data=image_data,
                        mime_type='image/png'  
                    )]
                )
            ]
            
            # Generate response
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=contents,
                config=types.GenerateContentConfig(response_modalities=[types.Modality.TEXT])
            )
            
            result_text = response.candidates[0].content.parts[0].text
            # Clean up the response
            cleaned_text = result_text.strip('```json').strip('```').strip()
            result_json = json.loads(cleaned_text)
            
            is_valid = result_json.get("valid", "No") == "Yes"
            reason = result_json.get("reason", "")
            
            return is_valid, reason
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False, "Error validating image"
    
    async def health_check(self) -> bool:
        """Check if Gemini service is healthy"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=[types.Content(role="user", parts=[types.Part(text="Hello")])],
                config=types.GenerateContentConfig(
                    response_modalities=[types.Modality.TEXT]
                )
            )
            return True
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False
    
    def _build_system_prompt(self, speciality: str, metadata: Dict[str, Any], message_count: int) -> str:
        """Build dynamic system prompt"""
        base = f"""You are a compassionate {speciality} health AI assistant.

CRITICAL RULES:
1. NEVER provide definitive diagnoses
2. NEVER recommend specific medications
3. ALWAYS encourage professional consultation
4. Be empathetic but professional
5. Ask focused, relevant questions
6. Keep responses concise (2-3 sentences)

Current Information Gathered:
- Age: {metadata.get('age', 'Not provided')}
- Gender: {metadata.get('gender', 'Not provided')}
- Symptoms: {', '.join(metadata.get('symptoms', []))}

Messages exchanged: {message_count}

"""
        
        if message_count < 3:
            base += "Focus on: Primary symptoms, location, duration, pain level"
        elif message_count < 6:
            base += "Focus on: Medical history, recent changes, previous treatments"
        else:
            base += "You should have enough information. Ask the user to upload an image of the affected area."
        
        return base
    
    def _extract_metadata(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Extract metadata from messages"""
        metadata = {}
        
        # Extract age
        age_match = re.search(r'\b(\d{1,3})\s*(?:year|yr|y\.o\.|years old)', user_message, re.IGNORECASE)
        if age_match:
            metadata['age'] = age_match.group(1)
        
        # Extract gender
        if re.search(r'\b(male|man|boy)\b', user_message, re.IGNORECASE):
            metadata['gender'] = 'male'
        elif re.search(r'\b(female|woman|girl)\b', user_message, re.IGNORECASE):
            metadata['gender'] = 'female'
        
        # Extract symptoms
        symptom_keywords = ['pain', 'itch', 'burning', 'swelling', 'redness', 'bleeding', 'growth', 'change']
        symptoms = [kw for kw in symptom_keywords if kw in user_message.lower()]
        if symptoms:
            metadata['symptoms'] = symptoms
        
        return metadata
    
    def _should_request_image(self, messages: List[Dict], metadata: Dict[str, Any]) -> bool:
        """Determine if we should request image upload"""
        if len(messages) < 6:
            return False
        
        # Check if already requested
        for msg in messages[-4:]:
            if 'upload' in msg['content'].lower() or 'image' in msg['content'].lower():
                return False
        
        # Check if enough info gathered
        required_info = ['age', 'symptoms']
        has_info = all(metadata.get(key) for key in required_info)
        
        return has_info

    async def generate_metadata_request(self, context_prompt: str) -> str:
        """Generate a dynamic metadata request using Gemini"""
        try:
            model = self.client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=[context_prompt],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=200,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            response_text = model.text.strip()
            logger.info(f"🤖 Generated dynamic metadata request: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating metadata request: {e}")
            # Return a simple dynamic response instead of raising error
            return "I'd like to learn more about your health. Could you share some additional information?"

    async def extract_metadata(self, extraction_prompt: str) -> str:
        """Extract metadata from user message using Gemini's natural language understanding"""
        try:
            model = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[extraction_prompt],
                config=types.GenerateContentConfig(
                    temperature=0.0,  # Zero temperature for maximum consistency
                    max_output_tokens=300,  # Reduced for focused extraction
                    top_p=0.8,
                    top_k=40
                )
            )
            
            response_text = model.text.strip()
            logger.info(f"🔍 Gemini metadata extraction response: {response_text[:150]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            # Return empty JSON instead of raising error
            return "{}"
    
    async def analyze_image_with_text(self, image_data: bytes, prompt: str) -> str:
        """Analyze image with text prompt using Gemini"""
        try:
            import base64
            
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create content with image and text
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text=prompt),
                        types.Part(
                            inline_data=types.InlineData(
                                mime_type="image/png",
                                data=image_base64
                            )
                        )
                    ]
                )
            ]
            
            # Generate response
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for medical analysis
                    max_output_tokens=1000,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            response_text = response.text.strip()
            logger.info(f"🖼️ Gemini image analysis response: {response_text[:200]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error analyzing image with Gemini: {e}")
            return "Unable to analyze the image. Please consult a healthcare professional for proper evaluation."
