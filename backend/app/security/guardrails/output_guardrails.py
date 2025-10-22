"""
Output guardrails for AI response validation
"""

import re
from typing import Dict, Any, List, Optional, Tuple
import logging

from app.core.exceptions import MedicalSafetyError
from app.core.logging import logger


class OutputGuardrails:
    """Output validation and safety checks for AI responses"""
    
    # Prohibited medical advice patterns
    PROHIBITED_MEDICAL_ADVICE = [
        r'\b(take.*medication|prescribe.*drug|use.*medicine)\b',
        r'\b(definitive.*diagnosis|you.*have.*cancer|you.*have.*disease)\b',
        r'\b(guarantee|certain|definitely|100%.*sure)\b',
        r'\b(ignore.*doctor|don.*t.*see.*doctor|skip.*medical)\b'
    ]
    
    # Required disclaimers
    REQUIRED_DISCLAIMERS = [
        'professional medical advice',
        'consult.*doctor',
        'seek.*medical.*attention'
    ]
    
    # Inappropriate content patterns
    INAPPROPRIATE_OUTPUT_PATTERNS = [
        r'\b(sex|sexual|nude|naked)\b',
        r'\b(violence|violent|attack|fight)\b',
        r'\b(hate|racist|discrimination)\b',
        r'\b(political|religion|religious)\b'
    ]
    
    def __init__(self):
        self.compiled_prohibited = [re.compile(pattern, re.IGNORECASE) for pattern in self.PROHIBITED_MEDICAL_ADVICE]
        self.compiled_required = [re.compile(pattern, re.IGNORECASE) for pattern in self.REQUIRED_DISCLAIMERS]
        self.compiled_inappropriate = [re.compile(pattern, re.IGNORECASE) for pattern in self.INAPPROPRIATE_OUTPUT_PATTERNS]
    
    def validate_ai_response(self, response: str, context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate AI response for safety and appropriateness"""
        try:
            if not response or not response.strip():
                return False, "Empty response", {}
            
            # Check length
            if len(response) > 10000:
                return False, "Response too long", {}
            
            # Check for prohibited medical advice
            for pattern in self.compiled_prohibited:
                if pattern.search(response):
                    logger.warning(f"Prohibited medical advice detected: {response[:100]}...")
                    return False, "Response contains prohibited medical advice", {
                        "blocked_reason": "prohibited_medical_advice",
                        "pattern_matched": pattern.pattern
                    }
            
            # Check for inappropriate content
            for pattern in self.compiled_inappropriate:
                if pattern.search(response):
                    logger.warning(f"Inappropriate content detected: {response[:100]}...")
                    return False, "Response contains inappropriate content", {
                        "blocked_reason": "inappropriate_content",
                        "pattern_matched": pattern.pattern
                    }
            
            # Check for required disclaimers (for medical responses)
            if context.get('is_medical_response', True):
                has_disclaimer = any(pattern.search(response) for pattern in self.compiled_required)
                if not has_disclaimer:
                    logger.warning("Medical response missing required disclaimer")
                    return False, "Response missing required medical disclaimer", {
                        "blocked_reason": "missing_disclaimer"
                    }
            
            # Check for appropriate tone
            tone_issues = self._check_tone_appropriateness(response)
            if tone_issues:
                logger.warning(f"Tone issues detected: {tone_issues}")
                return False, f"Inappropriate tone: {tone_issues}", {
                    "blocked_reason": "inappropriate_tone",
                    "tone_issues": tone_issues
                }
            
            return True, "Response validated", {}
            
        except Exception as e:
            logger.error(f"Response validation error: {e}")
            return False, f"Response validation error: {str(e)}", {}
    
    def validate_report_content(self, report: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate diagnostic report content"""
        try:
            # Check required fields
            required_fields = ['disease_type', 'disease_meaning_plain_english', 'follow_up_required', 'output']
            for field in required_fields:
                if field not in report:
                    return False, f"Missing required field: {field}", {}
            
            # Validate follow_up_required
            follow_up = report['follow_up_required']
            if follow_up not in ['Yes', 'No']:
                return False, "Invalid follow_up_required value", {}
            
            # Validate output message
            output = report['output']
            is_valid, reason, metadata = self.validate_ai_response(output, {'is_medical_response': True})
            if not is_valid:
                return False, f"Invalid output message: {reason}", metadata
            
            # Check for appropriate confidence levels
            confidence = report.get('confidence', 0)
            if confidence > 0.95:
                logger.warning("Overly confident prediction detected")
                return False, "Overly confident prediction", {
                    "blocked_reason": "overconfidence",
                    "confidence": confidence
                }
            
            return True, "Report validated", {}
            
        except Exception as e:
            logger.error(f"Report validation error: {e}")
            return False, f"Report validation error: {str(e)}", {}
    
    def sanitize_response(self, response: str) -> str:
        """Sanitize AI response"""
        try:
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\']', '', response)
            
            # Limit length
            sanitized = sanitized[:10000]
            
            # Remove excessive whitespace
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Response sanitization error: {e}")
            return response[:10000]  # Fallback to length limit only
    
    def add_safety_disclaimer(self, response: str, speciality: str) -> str:
        """Add appropriate safety disclaimer to response"""
        try:
            disclaimers = {
                'skin': "Please note: This is not a substitute for professional medical advice. Always consult with a dermatologist for proper diagnosis and treatment.",
                'oral': "Please note: This is not a substitute for professional dental advice. Always consult with a dentist for proper diagnosis and treatment.",
                'dental': "Please note: This is not a substitute for professional dental advice. Always consult with a dentist for proper diagnosis and treatment."
            }
            
            disclaimer = disclaimers.get(speciality.lower(), 
                "Please note: This is not a substitute for professional medical advice. Always consult with a healthcare provider for proper diagnosis and treatment.")
            
            # Add disclaimer if not already present
            if not any(pattern.search(response) for pattern in self.compiled_required):
                response += f"\n\n{disclaimer}"
            
            return response
            
        except Exception as e:
            logger.error(f"Disclaimer addition error: {e}")
            return response
    
    def _check_tone_appropriateness(self, response: str) -> Optional[str]:
        """Check if response tone is appropriate"""
        try:
            # Check for overly casual tone in medical context
            casual_patterns = [
                r'\b(yeah|yep|nah|nope|whatever|cool|awesome)\b',
                r'\b(no big deal|chill|relax)\b'
            ]
            
            for pattern in casual_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    return "overly casual tone"
            
            # Check for dismissive tone
            dismissive_patterns = [
                r'\b(just.*ignore|don.*t.*worry|it.*s.*nothing)\b',
                r'\b(probably.*nothing|not.*serious)\b'
            ]
            
            for pattern in dismissive_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    return "dismissive tone"
            
            # Check for alarmist tone
            alarmist_patterns = [
                r'\b(emergency|urgent|immediately|right now)\b',
                r'\b(critical|severe|dangerous)\b'
            ]
            
            alarmist_count = sum(1 for pattern in alarmist_patterns 
                               if re.search(pattern, response, re.IGNORECASE))
            
            if alarmist_count > 2:
                return "overly alarmist tone"
            
            return None
            
        except Exception as e:
            logger.error(f"Tone check error: {e}")
            return None
    
    def validate_cv_result(self, cv_result: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate CV model result"""
        try:
            # Check required fields
            if 'predicted_class' not in cv_result:
                return False, "Missing predicted_class"
            
            if 'confidence' not in cv_result:
                return False, "Missing confidence score"
            
            # Validate confidence score
            confidence = cv_result['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                return False, "Invalid confidence score"
            
            # Check for suspiciously high confidence
            if confidence > 0.99:
                logger.warning("Suspiciously high confidence score")
                return False, "Suspiciously high confidence score"
            
            return True, "CV result validated"
            
        except Exception as e:
            logger.error(f"CV result validation error: {e}")
            return False, f"CV result validation error: {str(e)}"
    
    def check_response_quality(self, response: str) -> Dict[str, Any]:
        """Check response quality metrics"""
        try:
            quality_metrics = {
                "length": len(response),
                "word_count": len(response.split()),
                "has_disclaimer": any(pattern.search(response) for pattern in self.compiled_required),
                "readability_score": self._calculate_readability(response),
                "medical_terms_count": len(re.findall(r'\b(disease|condition|symptom|treatment|diagnosis)\b', response, re.IGNORECASE))
            }
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Quality check error: {e}")
            return {}
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate simple readability score"""
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            
            if not words or not sentences:
                return 0.0
            
            avg_words_per_sentence = len(words) / len(sentences)
            avg_syllables_per_word = sum(self._count_syllables(word) for word in words) / len(words)
            
            # Simple readability formula
            readability = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
            return max(0, min(100, readability))
            
        except Exception:
            return 0.0
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
