"""
Prompt templates for different medical scenarios
"""

from typing import Dict, Any, List
from enum import Enum


class PromptTemplate:
    """Base class for prompt templates"""
    
    @staticmethod
    def get_system_prompt(speciality: str, metadata: Dict[str, Any], message_count: int) -> str:
        """Get system prompt based on context"""
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
    
    @staticmethod
    def get_report_generation_prompt(speciality: str, metadata: Dict[str, Any], cv_result: Dict[str, Any]) -> str:
        """Get prompt for report generation"""
        return f"""You are a {speciality} AI assistant. Generate a structured JSON report with:

{{
  "disease_type": "<Predicted condition>",
  "disease_meaning_plain_english": "<Simple explanation>",
  "follow_up_required": "<Yes or No>",
  "home_remedy_enough": "<Yes or No>",
  "home_remedy_details": "<If Yes, describe safe remedies>",
  "age": "{metadata.get('age', 'Not provided')}",
  "gender": "{metadata.get('gender', 'Not provided')}",
  "symptoms": {metadata.get('symptoms', [])},
  "other_information": "<Any other context>",
  "output": "<Single empathetic message for the user combining all info. DO NOT mention confidence scores.>"
}}

CV Model Output: {cv_result}

Rules:
- Return ONLY valid JSON
- Use plain English and empathetic tone
- If confidence is low, mark follow_up_required: "Yes"
- Be conservative with home remedies
- Always emphasize the importance of professional medical consultation
"""


class SkinPromptTemplate(PromptTemplate):
    """Specialized prompts for skin health"""
    
    @staticmethod
    def get_initial_greeting() -> str:
        """Get initial greeting for skin consultations"""
        return """Hello! I'm here to help you understand your skin concern. I can provide general information and guidance, but please remember that I cannot replace professional medical advice.

To help you better, I'll need to ask some questions about your symptoms. Let's start with the basics:

1. What skin changes are you noticing?
2. Where on your body is this occurring?
3. How long have you had these symptoms?

Please describe what you're experiencing in your own words."""

    @staticmethod
    def get_image_request_prompt() -> str:
        """Get prompt for requesting skin images"""
        return """Thank you for providing that information. To give you the most helpful guidance, it would be very helpful if you could upload a clear photo of the affected area.

For the best results, please:
- Take the photo in good lighting
- Make sure the area is clearly visible
- Include some surrounding normal skin for comparison
- Take the photo from a reasonable distance (not too close)

Once you upload the image, I can provide more specific information about what you're experiencing."""


class OralPromptTemplate(PromptTemplate):
    """Specialized prompts for oral health"""
    
    @staticmethod
    def get_initial_greeting() -> str:
        """Get initial greeting for oral health consultations"""
        return """Hello! I'm here to help you understand your oral health concern. I can provide general information and guidance, but please remember that I cannot replace professional dental advice.

To help you better, I'll need to ask some questions about your symptoms. Let's start with the basics:

1. What changes are you noticing in your mouth?
2. Are you experiencing any pain or discomfort?
3. How long have you had these symptoms?

Please describe what you're experiencing in your own words."""

    @staticmethod
    def get_image_request_prompt() -> str:
        """Get prompt for requesting oral images"""
        return """Thank you for providing that information. To give you the most helpful guidance, it would be very helpful if you could upload a clear photo of the affected area in your mouth.

For the best results, please:
- Take the photo in good lighting
- Make sure the area is clearly visible
- Try to keep your mouth open and still
- Include surrounding areas for context

Once you upload the image, I can provide more specific information about what you're experiencing."""


class PromptManager:
    """Manages different prompt templates"""
    
    TEMPLATES = {
        "skin": SkinPromptTemplate,
        "oral": OralPromptTemplate,
        "dental": OralPromptTemplate
    }
    
    @classmethod
    def get_template(cls, speciality: str) -> PromptTemplate:
        """Get appropriate template for speciality"""
        return cls.TEMPLATES.get(speciality.lower(), PromptTemplate)
    
    @classmethod
    def get_initial_greeting(cls, speciality: str) -> str:
        """Get initial greeting for speciality"""
        template = cls.get_template(speciality)
        if hasattr(template, 'get_initial_greeting'):
            return template.get_initial_greeting()
        return "Hello! I'm here to help you with your health concern. Please describe what you're experiencing."
    
    @classmethod
    def get_image_request_prompt(cls, speciality: str) -> str:
        """Get image request prompt for speciality"""
        template = cls.get_template(speciality)
        if hasattr(template, 'get_image_request_prompt'):
            return template.get_image_request_prompt()
        return "It would be helpful if you could upload a clear photo of the affected area for better analysis."
