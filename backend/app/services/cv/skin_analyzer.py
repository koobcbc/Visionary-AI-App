"""
Skin disease analyzer service
"""

from typing import Dict, Any, List, Optional
import logging

from app.core.exceptions import CVModelError
from app.core.logging import logger


class SkinAnalyzer:
    """Specialized analyzer for skin diseases"""
    
    SKIN_DISEASES = {
        "melanoma": {
            "severity": "high",
            "urgency": "immediate",
            "description": "A serious form of skin cancer",
            "recommendations": ["Seek immediate medical attention", "Avoid sun exposure"]
        },
        "basal_cell_carcinoma": {
            "severity": "medium",
            "urgency": "urgent",
            "description": "Most common form of skin cancer",
            "recommendations": ["Schedule dermatologist appointment", "Monitor for changes"]
        },
        "squamous_cell_carcinoma": {
            "severity": "medium",
            "urgency": "urgent", 
            "description": "Second most common skin cancer",
            "recommendations": ["Schedule dermatologist appointment", "Avoid sun exposure"]
        },
        "actinic_keratosis": {
            "severity": "low",
            "urgency": "routine",
            "description": "Precancerous skin condition",
            "recommendations": ["Schedule dermatologist appointment", "Use sunscreen"]
        },
        "seborrheic_keratosis": {
            "severity": "low",
            "urgency": "routine",
            "description": "Benign skin growth",
            "recommendations": ["Monitor for changes", "Optional removal if bothersome"]
        },
        "dermatofibroma": {
            "severity": "low",
            "urgency": "routine",
            "description": "Benign skin lesion",
            "recommendations": ["No treatment needed", "Monitor for changes"]
        },
        "nevus": {
            "severity": "low",
            "urgency": "routine",
            "description": "Mole or birthmark",
            "recommendations": ["Regular self-examination", "Annual skin check"]
        },
        "benign_keratosis": {
            "severity": "low",
            "urgency": "routine",
            "description": "Benign skin growth",
            "recommendations": ["No treatment needed", "Monitor for changes"]
        }
    }
    
    def analyze_result(self, cv_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CV model result for skin diseases"""
        try:
            predicted_class = cv_result.get("predicted_class", "").lower()
            confidence = cv_result.get("confidence", 0.0)
            
            # Get disease information
            disease_info = self.SKIN_DISEASES.get(predicted_class, {
                "severity": "unknown",
                "urgency": "routine",
                "description": "Unknown skin condition",
                "recommendations": ["Consult a dermatologist"]
            })
            
            # Determine follow-up urgency based on confidence and severity
            urgency = self._determine_urgency(confidence, disease_info["severity"])
            
            analysis = {
                "disease_type": predicted_class,
                "confidence": confidence,
                "severity": disease_info["severity"],
                "urgency": urgency,
                "description": disease_info["description"],
                "recommendations": disease_info["recommendations"],
                "follow_up_required": urgency in ["immediate", "urgent"],
                "home_remedy_enough": urgency == "routine" and confidence > 0.8
            }
            
            logger.info(f"Skin analysis completed: {predicted_class} (confidence: {confidence})")
            return analysis
            
        except Exception as e:
            logger.error(f"Skin analysis error: {e}")
            raise CVModelError(f"Skin analysis failed: {str(e)}")
    
    def _determine_urgency(self, confidence: float, severity: str) -> str:
        """Determine urgency based on confidence and severity"""
        if severity == "high":
            return "immediate"
        elif severity == "medium":
            if confidence > 0.7:
                return "urgent"
            else:
                return "routine"
        else:
            if confidence > 0.8:
                return "routine"
            else:
                return "urgent"
    
    def get_skin_care_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Get general skin care recommendations"""
        recommendations = [
            "Use broad-spectrum sunscreen (SPF 30+) daily",
            "Avoid peak sun hours (10 AM - 4 PM)",
            "Perform monthly self-skin examinations",
            "Schedule annual dermatologist visits",
            "Stay hydrated and maintain healthy diet"
        ]
        
        # Add specific recommendations based on analysis
        if analysis.get("severity") == "high":
            recommendations.insert(0, "Seek immediate medical attention")
        elif analysis.get("severity") == "medium":
            recommendations.insert(0, "Schedule dermatologist appointment within 1-2 weeks")
        
        return recommendations
