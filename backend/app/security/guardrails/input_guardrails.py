"""
Input guardrails for safety and validation
"""

import re
from typing import Dict, Any, List, Optional, Tuple
import logging

from app.core.exceptions import ValidationError, MedicalSafetyError
from app.core.logging import logger


class InputGuardrails:
    """Input validation and safety checks"""
    
    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        r'\b(suicide|kill.*self|end.*life)\b',
        r'\b(drug.*overdose|poison.*self)\b',
        r'\b(harm.*self|hurt.*self)\b',
        r'\b(illegal.*drug|prescription.*abuse)\b'
    ]
    
    # Medical emergency keywords
    MEDICAL_EMERGENCY_KEYWORDS = [
        'chest pain', 'heart attack', 'stroke', 'severe bleeding',
        'difficulty breathing', 'unconscious', 'severe allergic reaction',
        'severe burn', 'broken bone', 'head injury'
    ]
    
    # Inappropriate content patterns
    INAPPROPRIATE_PATTERNS = [
        r'\b(sex|sexual|nude|naked)\b',
        r'\b(violence|violent|attack|fight)\b',
        r'\b(hate|racist|discrimination)\b'
    ]
    
    def __init__(self):
        self.compiled_dangerous = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
        self.compiled_inappropriate = [re.compile(pattern, re.IGNORECASE) for pattern in self.INAPPROPRIATE_PATTERNS]
    
    def validate_text_input(self, text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate text input for safety and appropriateness"""
        try:
            if not text or not text.strip():
                return False, "Empty input", {}
            
            # Check length
            if len(text) > 5000:
                return False, "Input too long (max 5000 characters)", {}
            
            # Check for dangerous content
            for pattern in self.compiled_dangerous:
                if pattern.search(text):
                    logger.warning(f"Dangerous content detected: {text[:100]}...")
                    return False, "Content contains potentially harmful information", {
                        "blocked_reason": "dangerous_content",
                        "pattern_matched": pattern.pattern
                    }
            
            # Check for inappropriate content
            for pattern in self.compiled_inappropriate:
                if pattern.search(text):
                    logger.warning(f"Inappropriate content detected: {text[:100]}...")
                    return False, "Content contains inappropriate material", {
                        "blocked_reason": "inappropriate_content",
                        "pattern_matched": pattern.pattern
                    }
            
            # Check for medical emergencies
            emergency_detected = self._check_medical_emergency(text)
            if emergency_detected:
                return True, "Medical emergency detected", {
                    "emergency_detected": True,
                    "emergency_type": emergency_detected
                }
            
            return True, "Input validated", {}
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False, f"Validation error: {str(e)}", {}
    
    def validate_image_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate image metadata"""
        try:
            # Check required fields
            required_fields = ['filename', 'content_type', 'size']
            for field in required_fields:
                if field not in metadata:
                    return False, f"Missing required field: {field}"
            
            # Check file size
            if metadata.get('size', 0) > 10 * 1024 * 1024:  # 10MB
                return False, "File too large"
            
            # Check content type
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if metadata.get('content_type') not in allowed_types:
                return False, f"Unsupported file type: {metadata.get('content_type')}"
            
            # Check filename
            filename = metadata.get('filename', '')
            if not filename or len(filename) > 255:
                return False, "Invalid filename"
            
            return True, "Metadata validated"
            
        except Exception as e:
            logger.error(f"Metadata validation error: {e}")
            return False, f"Metadata validation error: {str(e)}"
    
    def validate_user_context(self, user_context: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate user context and session data"""
        try:
            # Check required fields
            if 'user_id' not in user_context:
                return False, "Missing user_id"
            
            if 'chat_id' not in user_context:
                return False, "Missing chat_id"
            
            # Validate user_id format
            user_id = user_context['user_id']
            if not isinstance(user_id, str) or len(user_id) < 1 or len(user_id) > 100:
                return False, "Invalid user_id format"
            
            # Validate chat_id format
            chat_id = user_context['chat_id']
            if not isinstance(chat_id, str) or len(chat_id) < 1 or len(chat_id) > 100:
                return False, "Invalid chat_id format"
            
            # Check for suspicious patterns in IDs
            if re.search(r'[<>"\']', user_id) or re.search(r'[<>"\']', chat_id):
                return False, "Invalid characters in user or chat ID"
            
            return True, "User context validated"
            
        except Exception as e:
            logger.error(f"User context validation error: {e}")
            return False, f"User context validation error: {str(e)}"
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize input text"""
        try:
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\']', '', text)
            
            # Limit length
            sanitized = sanitized[:5000]
            
            # Remove excessive whitespace
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Input sanitization error: {e}")
            return text[:5000]  # Fallback to length limit only
    
    def _check_medical_emergency(self, text: str) -> Optional[str]:
        """Check if text indicates a medical emergency"""
        text_lower = text.lower()
        
        for keyword in self.MEDICAL_EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                return keyword
        
        return None
    
    def validate_speciality(self, speciality: str) -> Tuple[bool, str]:
        """Validate medical speciality"""
        try:
            allowed_specialities = ['skin', 'oral', 'dental']
            
            if speciality.lower() not in allowed_specialities:
                return False, f"Unsupported speciality: {speciality}"
            
            return True, "Speciality validated"
            
        except Exception as e:
            logger.error(f"Speciality validation error: {e}")
            return False, f"Speciality validation error: {str(e)}"
    
    def check_rate_limit_violation(self, user_id: str, request_count: int, time_window: int) -> bool:
        """Check if user has exceeded rate limits"""
        try:
            # Basic rate limiting logic
            max_requests_per_minute = 60
            max_requests_per_hour = 1000
            
            if time_window <= 60:  # Per minute
                return request_count > max_requests_per_minute
            else:  # Per hour
                return request_count > max_requests_per_hour
                
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False  # Fail open for safety
    
    def validate_chat_message(self, message: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate chat message structure"""
        try:
            # Check required fields
            required_fields = ['role', 'content']
            for field in required_fields:
                if field not in message:
                    return False, f"Missing required field: {field}", {}
            
            # Validate role
            if message['role'] not in ['patient', 'assistant']:
                return False, "Invalid message role", {}
            
            # Validate content
            content = message['content']
            if not isinstance(content, str) or not content.strip():
                return False, "Empty message content", {}
            
            # Validate text content
            is_valid, reason, metadata = self.validate_text_input(content)
            if not is_valid:
                return False, reason, metadata
            
            return True, "Message validated", metadata
            
        except Exception as e:
            logger.error(f"Chat message validation error: {e}")
            return False, f"Message validation error: {str(e)}", {}
