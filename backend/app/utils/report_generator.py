"""
Report generation utilities
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from app.core.logging import logger
from app.models.enums import Severity


class ReportGenerator:
    """Generate comprehensive diagnostic reports"""
    
    def __init__(self):
        self.report_template = {
            "disease_type": "",
            "disease_meaning_plain_english": "",
            "follow_up_required": "",
            "home_remedy_enough": "",
            "home_remedy_details": "",
            "age": "",
            "gender": "",
            "symptoms": [],
            "other_information": "",
            "output": "",
            "confidence_scores": {},
            "recommendations": [],
            "severity": "",
            "urgency": ""
        }
    
    def generate_report(
        self, 
        chat_data: Dict[str, Any], 
        cv_result: Dict[str, Any], 
        llm_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        try:
            report = self.report_template.copy()
            
            # Extract data from different sources
            metadata = chat_data.get('metadata', {})
            messages = chat_data.get('messages', [])
            
            # Fill basic information
            report.update({
                "age": metadata.get('age', 'Not provided'),
                "gender": metadata.get('gender', 'Not provided'),
                "symptoms": metadata.get('symptoms', []),
                "disease_type": cv_result.get('predicted_class', 'Unknown'),
                "confidence_scores": {
                    "cv_model": cv_result.get('confidence', 0.0),
                    "llm_analysis": llm_analysis.get('confidence', 0.0)
                }
            })
            
            # Generate disease explanation
            report["disease_meaning_plain_english"] = self._generate_disease_explanation(
                cv_result.get('predicted_class', ''),
                metadata
            )
            
            # Determine follow-up requirements
            report["follow_up_required"] = self._determine_follow_up_requirement(
                cv_result, metadata
            )
            
            # Determine if home remedy is sufficient
            report["home_remedy_enough"] = self._determine_home_remedy_sufficiency(
                cv_result, metadata
            )
            
            # Generate home remedy details
            if report["home_remedy_enough"] == "Yes":
                report["home_remedy_details"] = self._generate_home_remedy_details(
                    cv_result.get('predicted_class', ''),
                    metadata
                )
            
            # Generate recommendations
            report["recommendations"] = self._generate_recommendations(
                cv_result, metadata, llm_analysis
            )
            
            # Determine severity and urgency
            report["severity"] = self._determine_severity(cv_result, metadata)
            report["urgency"] = self._determine_urgency(cv_result, metadata)
            
            # Generate other information
            report["other_information"] = self._generate_other_information(
                chat_data, cv_result, llm_analysis
            )
            
            # Generate final output message
            report["output"] = self._generate_output_message(report)
            
            logger.info(f"Report generated for disease: {report['disease_type']}")
            return report
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            raise
    
    def _generate_disease_explanation(self, disease_type: str, metadata: Dict[str, Any]) -> str:
        """Generate plain English explanation of disease"""
        explanations = {
            'melanoma': 'A serious form of skin cancer that develops from pigment-producing cells',
            'basal_cell_carcinoma': 'The most common type of skin cancer, usually slow-growing',
            'squamous_cell_carcinoma': 'A type of skin cancer that can grow quickly if not treated',
            'actinic_keratosis': 'Precancerous skin lesions caused by sun damage',
            'seborrheic_keratosis': 'Benign skin growths that are harmless but may be bothersome',
            'dermatofibroma': 'A harmless, firm bump that commonly appears on the legs',
            'nevus': 'A mole or birthmark, usually harmless but should be monitored',
            'gingivitis': 'Mild inflammation of the gums, often caused by poor oral hygiene',
            'periodontitis': 'Serious gum infection that can damage teeth and supporting structures',
            'oral_cancer': 'Cancerous growth in the mouth that requires immediate medical attention'
        }
        
        return explanations.get(disease_type.lower(), f'A {disease_type} condition that requires medical evaluation')
    
    def _determine_follow_up_requirement(self, cv_result: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Determine if follow-up is required"""
        predicted_class = cv_result.get('predicted_class', '').lower()
        confidence = cv_result.get('confidence', 0.0)
        
        # High-risk conditions always require follow-up
        high_risk_conditions = ['melanoma', 'cancer', 'malignant', 'oral_cancer']
        if any(condition in predicted_class for condition in high_risk_conditions):
            return "Yes"
        
        # Medium-risk conditions require follow-up if confidence is high
        medium_risk_conditions = ['squamous_cell_carcinoma', 'basal_cell_carcinoma', 'periodontitis']
        if any(condition in predicted_class for condition in medium_risk_conditions):
            return "Yes" if confidence > 0.7 else "Yes"  # Always recommend follow-up for these
        
        # Low-risk conditions may not require immediate follow-up
        low_risk_conditions = ['seborrheic_keratosis', 'dermatofibroma', 'nevus', 'gingivitis']
        if any(condition in predicted_class for condition in low_risk_conditions):
            return "No" if confidence > 0.8 else "Yes"
        
        # Default to requiring follow-up for safety
        return "Yes"
    
    def _determine_home_remedy_sufficiency(self, cv_result: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Determine if home remedy is sufficient"""
        predicted_class = cv_result.get('predicted_class', '').lower()
        confidence = cv_result.get('confidence', 0.0)
        
        # Never recommend home remedies for high-risk conditions
        high_risk_conditions = ['melanoma', 'cancer', 'malignant', 'oral_cancer']
        if any(condition in predicted_class for condition in high_risk_conditions):
            return "No"
        
        # Medium-risk conditions should not rely on home remedies
        medium_risk_conditions = ['squamous_cell_carcinoma', 'basal_cell_carcinoma', 'periodontitis']
        if any(condition in predicted_class for condition in medium_risk_conditions):
            return "No"
        
        # Low-risk conditions may benefit from home remedies
        low_risk_conditions = ['seborrheic_keratosis', 'dermatofibroma', 'nevus', 'gingivitis']
        if any(condition in predicted_class for condition in low_risk_conditions):
            return "Yes" if confidence > 0.8 else "No"
        
        # Default to not recommending home remedies
        return "No"
    
    def _generate_home_remedy_details(self, disease_type: str, metadata: Dict[str, Any]) -> str:
        """Generate home remedy details"""
        remedies = {
            'gingivitis': 'Improve oral hygiene by brushing twice daily, flossing, and using antiseptic mouthwash. Avoid tobacco and maintain a healthy diet.',
            'seborrheic_keratosis': 'These are harmless growths that don\'t require treatment. If bothersome, consult a dermatologist for removal options.',
            'dermatofibroma': 'These harmless bumps don\'t require treatment. Avoid picking or scratching the area.',
            'nevus': 'Monitor moles for changes in size, color, or shape. Use sunscreen and avoid excessive sun exposure.',
            'actinic_keratosis': 'Use sunscreen daily, avoid peak sun hours, and wear protective clothing. Consider dermatologist evaluation.'
        }
        
        return remedies.get(disease_type.lower(), 'Consult with a healthcare provider for appropriate treatment recommendations.')
    
    def _generate_recommendations(self, cv_result: Dict[str, Any], metadata: Dict[str, Any], llm_analysis: Dict[str, Any]) -> List[str]:
        """Generate medical recommendations"""
        recommendations = []
        predicted_class = cv_result.get('predicted_class', '').lower()
        confidence = cv_result.get('confidence', 0.0)
        
        # General recommendations
        recommendations.append("Consult with a healthcare provider for proper diagnosis and treatment")
        
        # Specific recommendations based on condition
        if 'melanoma' in predicted_class or 'cancer' in predicted_class:
            recommendations.append("Seek immediate medical attention")
            recommendations.append("Avoid sun exposure and use broad-spectrum sunscreen")
        elif 'gingivitis' in predicted_class or 'periodontitis' in predicted_class:
            recommendations.append("Improve oral hygiene practices")
            recommendations.append("Schedule dental cleaning and evaluation")
        elif 'actinic_keratosis' in predicted_class:
            recommendations.append("Use sunscreen daily")
            recommendations.append("Consider dermatologist evaluation")
        
        # Confidence-based recommendations
        if confidence < 0.7:
            recommendations.append("Consider getting a second opinion")
        
        return recommendations
    
    def _determine_severity(self, cv_result: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Determine condition severity"""
        predicted_class = cv_result.get('predicted_class', '').lower()
        
        if any(condition in predicted_class for condition in ['melanoma', 'cancer', 'malignant', 'oral_cancer']):
            return Severity.CRITICAL.value
        elif any(condition in predicted_class for condition in ['squamous_cell_carcinoma', 'basal_cell_carcinoma', 'periodontitis']):
            return Severity.HIGH.value
        elif any(condition in predicted_class for condition in ['actinic_keratosis', 'leukoplakia']):
            return Severity.MEDIUM.value
        else:
            return Severity.LOW.value
    
    def _determine_urgency(self, cv_result: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Determine urgency of medical attention"""
        predicted_class = cv_result.get('predicted_class', '').lower()
        confidence = cv_result.get('confidence', 0.0)
        
        if any(condition in predicted_class for condition in ['melanoma', 'cancer', 'malignant', 'oral_cancer']):
            return "immediate"
        elif any(condition in predicted_class for condition in ['squamous_cell_carcinoma', 'basal_cell_carcinoma']):
            return "urgent" if confidence > 0.7 else "routine"
        elif any(condition in predicted_class for condition in ['periodontitis', 'actinic_keratosis']):
            return "urgent"
        else:
            return "routine"
    
    def _generate_other_information(self, chat_data: Dict[str, Any], cv_result: Dict[str, Any], llm_analysis: Dict[str, Any]) -> str:
        """Generate additional context information"""
        info_parts = []
        
        # Add confidence information
        confidence = cv_result.get('confidence', 0.0)
        if confidence < 0.7:
            info_parts.append("Low confidence prediction - consider additional evaluation")
        
        # Add chat context
        message_count = len(chat_data.get('messages', []))
        if message_count > 10:
            info_parts.append("Comprehensive conversation history available")
        
        # Add metadata context
        metadata = chat_data.get('metadata', {})
        if metadata.get('medical_history'):
            info_parts.append("Patient medical history considered")
        
        return '; '.join(info_parts) if info_parts else "Standard analysis performed"
    
    def _generate_output_message(self, report: Dict[str, Any]) -> str:
        """Generate final empathetic output message"""
        try:
            disease_type = report.get('disease_type', 'condition')
            follow_up = report.get('follow_up_required', 'Yes')
            home_remedy = report.get('home_remedy_enough', 'No')
            
            # Base message
            message = f"Based on the analysis, this appears to be {disease_type}. "
            
            # Add explanation
            explanation = report.get('disease_meaning_plain_english', '')
            if explanation:
                message += f"{explanation}. "
            
            # Add follow-up recommendation
            if follow_up == "Yes":
                message += "I strongly recommend consulting with a healthcare provider for proper evaluation and treatment. "
            else:
                message += "While this appears to be a benign condition, it's always good to have it checked by a professional. "
            
            # Add home remedy information
            if home_remedy == "Yes":
                remedy_details = report.get('home_remedy_details', '')
                if remedy_details:
                    message += f"In the meantime, you can try: {remedy_details}. "
            
            # Add disclaimer
            message += "Please remember that this is not a substitute for professional medical advice."
            
            return message
            
        except Exception as e:
            logger.error(f"Output message generation error: {e}")
            return "Analysis completed. Please consult with a healthcare provider for proper evaluation and treatment."
    
    def format_report_for_display(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Format report for display purposes"""
        try:
            formatted_report = report.copy()
            
            # Format confidence scores as percentages
            if 'confidence_scores' in formatted_report:
                for key, value in formatted_report['confidence_scores'].items():
                    if isinstance(value, (int, float)):
                        formatted_report['confidence_scores'][key] = f"{value:.1%}"
            
            # Format symptoms as comma-separated string
            if 'symptoms' in formatted_report and isinstance(formatted_report['symptoms'], list):
                formatted_report['symptoms_display'] = ', '.join(formatted_report['symptoms'])
            
            # Format recommendations as numbered list
            if 'recommendations' in formatted_report and isinstance(formatted_report['recommendations'], list):
                formatted_report['recommendations_display'] = [
                    f"{i+1}. {rec}" for i, rec in enumerate(formatted_report['recommendations'])
                ]
            
            # Add timestamp
            formatted_report['generated_at'] = datetime.utcnow().isoformat()
            
            return formatted_report
            
        except Exception as e:
            logger.error(f"Report formatting error: {e}")
            return report
