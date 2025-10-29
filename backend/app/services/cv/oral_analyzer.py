"""
Oral health analyzer service
"""

from typing import Dict, Any, List, Optional
import logging

from app.core.exceptions import CVModelError
from app.core.logging import logger


class OralAnalyzer:
    """Specialized analyzer for oral health conditions"""
    
    ORAL_CONDITIONS = {
        "gingivitis": {
            "severity": "low",
            "urgency": "routine",
            "description": "Mild inflammation of the gums",
            "recommendations": ["Improve oral hygiene", "Use antiseptic mouthwash", "Schedule dental cleaning"]
        },
        "periodontitis": {
            "severity": "medium",
            "urgency": "urgent",
            "description": "Serious gum infection that damages soft tissue",
            "recommendations": ["Seek dental treatment", "Professional cleaning", "Antibiotic treatment if needed"]
        },
        "oral_cancer": {
            "severity": "high",
            "urgency": "immediate",
            "description": "Cancerous growth in the mouth",
            "recommendations": ["Seek immediate medical attention", "Biopsy if recommended", "Avoid tobacco and alcohol"]
        },
        "leukoplakia": {
            "severity": "medium",
            "urgency": "urgent",
            "description": "White patches that may be precancerous",
            "recommendations": ["Biopsy recommended", "Avoid tobacco", "Regular monitoring"]
        },
        "oral_thrush": {
            "severity": "low",
            "urgency": "routine",
            "description": "Fungal infection causing white lesions",
            "recommendations": ["Antifungal medication", "Improve oral hygiene", "Address underlying causes"]
        },
        "canker_sore": {
            "severity": "low",
            "urgency": "routine",
            "description": "Painful ulcer in the mouth",
            "recommendations": ["Topical treatments", "Avoid spicy foods", "Usually heals in 1-2 weeks"]
        },
        "cold_sore": {
            "severity": "low",
            "urgency": "routine",
            "description": "Viral infection causing blisters",
            "recommendations": ["Antiviral medication", "Keep area clean", "Avoid sharing utensils"]
        },
        "tooth_decay": {
            "severity": "medium",
            "urgency": "urgent",
            "description": "Cavities or dental caries",
            "recommendations": ["Dental filling", "Root canal if needed", "Improve oral hygiene"]
        },
        "normal": {
            "severity": "low",
            "urgency": "routine",
            "description": "Normal oral health",
            "recommendations": ["Maintain good oral hygiene", "Regular dental checkups", "Continue current care"]
        }
    }
    
    def analyze_result(self, cv_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CV model result for oral conditions"""
        try:
            predicted_class = cv_result.get("predicted_class", "").lower()
            confidence = cv_result.get("confidence", 0.0)
            
            # Get condition information
            condition_info = self.ORAL_CONDITIONS.get(predicted_class, {
                "severity": "unknown",
                "urgency": "routine",
                "description": "Unknown oral condition",
                "recommendations": ["Consult a dentist"]
            })
            
            # Determine follow-up urgency based on confidence and severity
            urgency = self._determine_urgency(confidence, condition_info["severity"])
            
            analysis = {
                "condition_type": predicted_class,
                "confidence": confidence,
                "severity": condition_info["severity"],
                "urgency": urgency,
                "description": condition_info["description"],
                "recommendations": condition_info["recommendations"],
                "follow_up_required": urgency in ["immediate", "urgent"],
                "home_remedy_enough": urgency == "routine" and confidence > 0.8
            }
            
            logger.info(f"Oral analysis completed: {predicted_class} (confidence: {confidence})")
            return analysis
            
        except Exception as e:
            logger.error(f"Oral analysis error: {e}")
            raise CVModelError(f"Oral analysis failed: {str(e)}")
    
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
    
    def get_oral_hygiene_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Get general oral hygiene recommendations"""
        recommendations = [
            "Brush teeth twice daily with fluoride toothpaste",
            "Floss daily to remove plaque between teeth",
            "Use antiseptic mouthwash",
            "Limit sugary foods and drinks",
            "Schedule regular dental checkups every 6 months",
            "Avoid tobacco products",
            "Stay hydrated to maintain saliva production"
        ]
        
        # Add specific recommendations based on analysis
        if analysis.get("severity") == "high":
            recommendations.insert(0, "Seek immediate medical attention")
        elif analysis.get("severity") == "medium":
            recommendations.insert(0, "Schedule dental appointment within 1-2 weeks")
        
        return recommendations
    
    def get_dietary_recommendations(self, condition: str) -> List[str]:
        """Get dietary recommendations for specific oral conditions"""
        dietary_guidelines = {
            "gingivitis": [
                "Increase vitamin C intake (citrus fruits, berries)",
                "Eat crunchy fruits and vegetables",
                "Limit sugary snacks"
            ],
            "oral_thrush": [
                "Avoid sugary foods that feed yeast",
                "Include probiotic foods (yogurt, kefir)",
                "Limit refined carbohydrates"
            ],
            "canker_sore": [
                "Avoid spicy and acidic foods",
                "Eat soft, bland foods",
                "Increase B-vitamin intake"
            ],
            "tooth_decay": [
                "Limit sugary and acidic foods",
                "Eat calcium-rich foods",
                "Avoid frequent snacking"
            ]
        }
        
        return dietary_guidelines.get(condition.lower(), [
            "Maintain balanced diet",
            "Limit sugary foods",
            "Eat plenty of fruits and vegetables"
        ])
