"""
Medical-specific guardrails and safety checks
"""

import re
from typing import Dict, Any, List, Optional, Tuple
import logging

from app.core.exceptions import MedicalSafetyError
from app.core.logging import logger


class MedicalGuardrails:
    """Medical-specific safety and validation guardrails"""
    
    # High-risk conditions that require immediate attention
    HIGH_RISK_CONDITIONS = [
        'melanoma', 'cancer', 'malignant', 'squamous cell carcinoma',
        'basal cell carcinoma', 'oral cancer', 'leukoplakia'
    ]
    
    # Emergency symptoms
    EMERGENCY_SYMPTOMS = [
        'severe pain', 'bleeding', 'swelling', 'difficulty breathing',
        'chest pain', 'severe allergic reaction', 'loss of consciousness'
    ]
    
    # Prohibited medical advice patterns
    PROHIBITED_ADVICE_PATTERNS = [
        r'\b(take.*medication|prescribe.*drug|use.*medicine)\b',
        r'\b(definitive.*diagnosis|you.*have.*cancer|you.*have.*disease)\b',
        r'\b(guarantee|certain|definitely|100%.*sure)\b',
        r'\b(ignore.*doctor|don.*t.*see.*doctor|skip.*medical)\b'
    ]
    
    # Required safety disclaimers
    REQUIRED_DISCLAIMERS = [
        'not.*substitute.*professional.*medical',
        'consult.*doctor',
        'seek.*medical.*attention',
        'professional.*medical.*advice'
    ]
    
    def __init__(self):
        self.compiled_prohibited = [re.compile(pattern, re.IGNORECASE) for pattern in self.PROHIBITED_ADVICE_PATTERNS]
        self.compiled_required = [re.compile(pattern, re.IGNORECASE) for pattern in self.REQUIRED_DISCLAIMERS]
    
    def validate_medical_response(self, response: str, speciality: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate medical response for safety and appropriateness"""
        try:
            # Check for prohibited medical advice
            for pattern in self.compiled_prohibited:
                if pattern.search(response):
                    logger.warning(f"Prohibited medical advice detected: {response[:100]}...")
                    return False, "Response contains prohibited medical advice", {
                        "blocked_reason": "prohibited_medical_advice",
                        "pattern_matched": pattern.pattern
                    }
            
            # Check for required disclaimers
            has_disclaimer = any(pattern.search(response) for pattern in self.compiled_required)
            if not has_disclaimer:
                logger.warning("Medical response missing required disclaimer")
                return False, "Response missing required medical disclaimer", {
                    "blocked_reason": "missing_disclaimer"
                }
            
            # Check for appropriate medical terminology
            terminology_check = self._check_medical_terminology(response, speciality)
            if not terminology_check["is_appropriate"]:
                return False, terminology_check["reason"], {
                    "blocked_reason": "inappropriate_terminology",
                    "issues": terminology_check["issues"]
                }
            
            # Check for emergency detection
            emergency_detected = self._detect_medical_emergency(response)
            if emergency_detected:
                return True, "Medical emergency detected", {
                    "emergency_detected": True,
                    "emergency_type": emergency_detected,
                    "requires_immediate_attention": True
                }
            
            return True, "Medical response validated", {}
            
        except Exception as e:
            logger.error(f"Medical response validation error: {e}")
            return False, f"Medical response validation error: {str(e)}", {}
    
    def validate_diagnostic_report(self, report: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate diagnostic report for medical safety"""
        try:
            # Check required fields
            required_fields = ['disease_type', 'follow_up_required', 'output']
            for field in required_fields:
                if field not in report:
                    return False, f"Missing required field: {field}", {}
            
            # Validate disease type
            disease_type = report.get('disease_type', '').lower()
            if disease_type in self.HIGH_RISK_CONDITIONS:
                logger.warning(f"High-risk condition detected: {disease_type}")
                # Ensure follow-up is required for high-risk conditions
                if report.get('follow_up_required', '').lower() != 'yes':
                    return False, "High-risk condition requires follow-up", {
                        "blocked_reason": "high_risk_no_followup",
                        "disease_type": disease_type
                    }
            
            # Validate follow-up requirement
            follow_up = report.get('follow_up_required', '').lower()
            if follow_up not in ['yes', 'no']:
                return False, "Invalid follow_up_required value", {}
            
            # Validate output message
            output = report.get('output', '')
            is_valid, reason, metadata = self.validate_medical_response(output, 'general')
            if not is_valid:
                return False, f"Invalid output message: {reason}", metadata
            
            # Check confidence levels
            confidence = report.get('confidence', 0)
            if confidence > 0.95:
                logger.warning("Overly confident medical prediction")
                return False, "Overly confident medical prediction", {
                    "blocked_reason": "overconfidence",
                    "confidence": confidence
                }
            
            return True, "Diagnostic report validated", {}
            
        except Exception as e:
            logger.error(f"Diagnostic report validation error: {e}")
            return False, f"Diagnostic report validation error: {str(e)}", {}
    
    def _check_medical_terminology(self, response: str, speciality: str) -> Dict[str, Any]:
        """Check if medical terminology is appropriate"""
        try:
            issues = []
            
            # Check for overly technical language
            technical_terms = [
                'pathophysiology', 'etiology', 'pathogenesis', 'histopathology',
                'immunohistochemistry', 'molecular biology', 'genetic mutation'
            ]
            
            technical_count = sum(1 for term in technical_terms if term.lower() in response.lower())
            if technical_count > 2:
                issues.append("overly technical language")
            
            # Check for inappropriate casual language
            casual_terms = [
                'yeah', 'yep', 'nah', 'nope', 'whatever', 'cool', 'awesome',
                'no big deal', 'chill', 'relax'
            ]
            
            casual_count = sum(1 for term in casual_terms if term.lower() in response.lower())
            if casual_count > 0:
                issues.append("inappropriate casual language")
            
            # Check for dismissive language
            dismissive_patterns = [
                r'\b(just.*ignore|don.*t.*worry|it.*s.*nothing)\b',
                r'\b(probably.*nothing|not.*serious)\b'
            ]
            
            for pattern in dismissive_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    issues.append("dismissive language")
                    break
            
            return {
                "is_appropriate": len(issues) == 0,
                "issues": issues,
                "reason": f"Inappropriate terminology: {', '.join(issues)}" if issues else "Terminology appropriate"
            }
            
        except Exception as e:
            logger.error(f"Medical terminology check error: {e}")
            return {
                "is_appropriate": True,
                "issues": [],
                "reason": "Terminology check failed"
            }
    
    def _detect_medical_emergency(self, response: str) -> Optional[str]:
        """Detect if response indicates a medical emergency"""
        try:
            response_lower = response.lower()
            
            for symptom in self.EMERGENCY_SYMPTOMS:
                if symptom in response_lower:
                    return symptom
            
            # Check for emergency keywords
            emergency_keywords = [
                'emergency', 'urgent', 'immediately', 'right now',
                'call 911', 'go to hospital', 'emergency room'
            ]
            
            for keyword in emergency_keywords:
                if keyword in response_lower:
                    return keyword
            
            return None
            
        except Exception as e:
            logger.error(f"Emergency detection error: {e}")
            return None
    
    def add_medical_disclaimer(self, response: str, speciality: str) -> str:
        """Add appropriate medical disclaimer to response"""
        try:
            disclaimers = {
                'skin': "⚠️ **Important**: This is not a substitute for professional medical advice. Always consult with a dermatologist for proper diagnosis and treatment.",
                'oral': "⚠️ **Important**: This is not a substitute for professional dental advice. Always consult with a dentist for proper diagnosis and treatment.",
                'dental': "⚠️ **Important**: This is not a substitute for professional dental advice. Always consult with a dentist for proper diagnosis and treatment."
            }
            
            disclaimer = disclaimers.get(speciality.lower(), 
                "⚠️ **Important**: This is not a substitute for professional medical advice. Always consult with a healthcare provider for proper diagnosis and treatment.")
            
            # Add disclaimer if not already present
            if not any(pattern.search(response) for pattern in self.compiled_required):
                response += f"\n\n{disclaimer}"
            
            return response
            
        except Exception as e:
            logger.error(f"Medical disclaimer addition error: {e}")
            return response
    
    def validate_cv_result_safety(self, cv_result: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate CV model result for medical safety"""
        try:
            # Check for high-risk predictions
            predicted_class = cv_result.get('predicted_class', '').lower()
            confidence = cv_result.get('confidence', 0)
            
            if predicted_class in self.HIGH_RISK_CONDITIONS:
                if confidence > 0.8:
                    logger.warning(f"High-risk condition predicted with high confidence: {predicted_class}")
                    return True, "High-risk condition detected - requires immediate medical attention"
                elif confidence > 0.5:
                    logger.warning(f"High-risk condition predicted with moderate confidence: {predicted_class}")
                    return True, "Possible high-risk condition - urgent medical evaluation recommended"
            
            # Check for suspiciously high confidence
            if confidence > 0.99:
                logger.warning("Suspiciously high confidence score")
                return False, "Suspiciously high confidence score"
            
            # Check for suspiciously low confidence
            if confidence < 0.1:
                logger.warning("Suspiciously low confidence score")
                return False, "Suspiciously low confidence score"
            
            return True, "CV result validated"
            
        except Exception as e:
            logger.error(f"CV result safety validation error: {e}")
            return False, f"CV result safety validation error: {str(e)}"
    
    def get_medical_safety_score(self, response: str, speciality: str) -> Dict[str, Any]:
        """Calculate medical safety score for response"""
        try:
            safety_metrics = {
                "has_disclaimer": any(pattern.search(response) for pattern in self.compiled_required),
                "no_prohibited_advice": not any(pattern.search(response) for pattern in self.compiled_prohibited),
                "appropriate_tone": self._check_appropriate_tone(response),
                "emergency_detection": self._detect_medical_emergency(response) is not None,
                "medical_terminology_appropriate": self._check_medical_terminology(response, speciality)["is_appropriate"]
            }
            
            # Calculate overall safety score
            safety_score = sum(safety_metrics.values()) / len(safety_metrics)
            
            return {
                "safety_score": safety_score,
                "metrics": safety_metrics,
                "recommendations": self._get_safety_recommendations(safety_metrics)
            }
            
        except Exception as e:
            logger.error(f"Medical safety score calculation error: {e}")
            return {"safety_score": 0.0, "metrics": {}, "recommendations": []}
    
    def _check_appropriate_tone(self, response: str) -> bool:
        """Check if response tone is appropriate for medical context"""
        try:
            # Check for empathetic language
            empathetic_words = ['understand', 'concern', 'care', 'help', 'support']
            has_empathetic_language = any(word in response.lower() for word in empathetic_words)
            
            # Check for professional language
            professional_words = ['recommend', 'suggest', 'advise', 'consult', 'evaluate']
            has_professional_language = any(word in response.lower() for word in professional_words)
            
            return has_empathetic_language and has_professional_language
            
        except Exception:
            return False
    
    def _get_safety_recommendations(self, safety_metrics: Dict[str, bool]) -> List[str]:
        """Get safety recommendations based on metrics"""
        recommendations = []
        
        if not safety_metrics.get("has_disclaimer", False):
            recommendations.append("Add medical disclaimer")
        
        if not safety_metrics.get("no_prohibited_advice", True):
            recommendations.append("Remove prohibited medical advice")
        
        if not safety_metrics.get("appropriate_tone", False):
            recommendations.append("Improve tone to be more empathetic and professional")
        
        if not safety_metrics.get("medical_terminology_appropriate", True):
            recommendations.append("Use more appropriate medical terminology")
        
        return recommendations
