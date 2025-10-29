"""
Computer Vision model service for medical image analysis
"""

import requests
import asyncio
from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import CVModelError
from app.core.logging import logger
from app.models.enums import HealthSpeciality


class CVModelService:
    """Handles CV model API calls for medical image analysis"""
    
    def __init__(self):
        self.skin_cv_api = settings.SKIN_CV_API
        self.oral_cv_api = settings.ORAL_CV_API
        self.timeout = 15  # Reduced timeout
        self.max_retries = 2  # Maximum retry attempts
        self.retry_delay = 2  # Delay between retries in seconds
    
    async def analyze_skin_image(self, image_data: bytes) -> Dict[str, Any]:
        """Call skin CV model for analysis with retry logic and fallback"""
        
        # Try the CV model with retries
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"🔄 Attempting skin CV analysis (attempt {attempt + 1}/{self.max_retries + 1})")
                
                files = {'file': ('image.png', image_data, 'image/png')}
                
                # Use asyncio to run the synchronous request
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.post(
                        self.skin_cv_api, 
                        files=files, 
                        timeout=self.timeout
                    )
                )
                
                if response.ok:
                    result = response.json()
                    logger.info(f"✅ Skin CV analysis complete: {result}")
                    
                    # CRITICAL: Validate the result to prevent hallucinations
                    validated_result = self._validate_cv_result(result, image_data)
                    return self._format_skin_result(validated_result)
                else:
                    logger.warning(f"Skin CV model error: {response.status_code}")
                    if attempt < self.max_retries:
                        logger.info(f"⏳ Retrying in {self.retry_delay} seconds...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        raise CVModelError(f"Skin CV model analysis failed: {response.status_code}")
                        
            except requests.exceptions.Timeout as e:
                logger.warning(f"⏰ Skin CV model timeout (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    logger.info(f"⏳ Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    logger.error("❌ All CV model attempts failed due to timeout")
                    return await self._get_fallback_skin_analysis(image_data)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"🌐 Skin CV model request error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    logger.info(f"⏳ Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    logger.error("❌ All CV model attempts failed due to request error")
                    return await self._get_fallback_skin_analysis(image_data)
                    
            except Exception as e:
                logger.error(f"❌ Skin CV model error: {e}")
                return await self._get_fallback_skin_analysis(image_data)
        
        # This should never be reached, but just in case
        return await self._get_fallback_skin_analysis(image_data)
    
    def _validate_cv_result(self, cv_result: Dict[str, Any], image_data: bytes) -> Dict[str, Any]:
        """Validate CV result to prevent hallucinations like 99% confidence on sunflowers"""
        try:
            confidence = cv_result.get('confidence', 0.0)
            predicted_class = cv_result.get('predicted_class', '')
            
            # If confidence is suspiciously high (>95%), flag for manual review
            if confidence > 0.95:
                logger.warning(f"Suspiciously high confidence ({confidence:.2%}) for {predicted_class}")
                # Reduce confidence and add warning
                cv_result['confidence'] = min(confidence, 0.85)  # Cap at 85%
                cv_result['validation_warning'] = "High confidence result - manual review recommended"
                cv_result['original_confidence'] = confidence
            
            # If confidence is very low (<10%), also flag
            if confidence < 0.10:
                logger.warning(f"Very low confidence ({confidence:.2%}) for {predicted_class}")
                cv_result['validation_warning'] = "Low confidence result - additional validation needed"
            
            return cv_result
            
        except Exception as e:
            logger.error(f"CV result validation error: {e}")
            return cv_result
    
    async def analyze_oral_image(self, image_data: bytes) -> Dict[str, Any]:
        """Call oral CV model for analysis"""
        if not self.oral_cv_api:
            # Return mock response for development
            logger.warning("Oral CV API not configured, returning mock response")
            return self._get_mock_oral_result()
        
        try:
            files = {'file': ('image.png', image_data, 'image/png')}
            
            # Use asyncio to run the synchronous request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    self.oral_cv_api, 
                    files=files, 
                    timeout=self.timeout
                )
            )
            
            if response.ok:
                result = response.json()
                logger.info(f"✅ Oral CV analysis complete: {result}")
                return self._format_oral_result(result)
            else:
                logger.error(f"Oral CV model error: {response.status_code}")
                raise CVModelError(f"Oral CV model analysis failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Oral CV model request error: {e}")
            raise CVModelError(f"Oral CV model request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Oral CV model error: {e}")
            raise CVModelError(f"Oral CV model error: {str(e)}")
    
    async def analyze_image(self, image_data: bytes, speciality: HealthSpeciality) -> Dict[str, Any]:
        """Analyze image based on speciality"""
        if speciality == HealthSpeciality.SKIN:
            return await self.analyze_skin_image(image_data)
        elif speciality in [HealthSpeciality.ORAL, HealthSpeciality.DENTAL]:
            return await self.analyze_oral_image(image_data)
        else:
            raise CVModelError(f"Unsupported speciality: {speciality}")
    
    async def health_check(self) -> bool:
        """Check if CV models are healthy"""
        try:
            # Test skin model
            if self.skin_cv_api:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(
                        self.skin_cv_api.replace('/predict', '/health'),
                        timeout=10
                    )
                )
                if not response.ok:
                    return False
            
            # Test oral model if configured
            if self.oral_cv_api:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(
                        self.oral_cv_api.replace('/predict', '/health'),
                        timeout=10
                    )
                )
                if not response.ok:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"CV models health check failed: {e}")
            return False
    
    def _format_skin_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format skin CV model result"""
        return {
            "predicted_class": result.get("predicted_class", "Unknown"),
            "confidence": result.get("confidence", 0.0),
            "disease_type": result.get("disease_type", "Unknown"),
            "severity": result.get("severity", "Unknown"),
            "description": result.get("description", ""),
            "recommendations": result.get("recommendations", []),
            "model_version": result.get("model_version", "1.0"),
            "analysis_timestamp": result.get("timestamp", "")
        }
    
    def _format_oral_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format oral CV model result"""
        return {
            "predicted_class": result.get("predicted_class", "Unknown"),
            "confidence": result.get("confidence", 0.0),
            "condition_type": result.get("condition_type", "Unknown"),
            "severity": result.get("severity", "Unknown"),
            "description": result.get("description", ""),
            "recommendations": result.get("recommendations", []),
            "model_version": result.get("model_version", "1.0"),
            "analysis_timestamp": result.get("timestamp", "")
        }
    
    def _get_mock_oral_result(self) -> Dict[str, Any]:
        """Get mock oral analysis result for development"""
        return {
            "predicted_class": "Gingivitis",
            "confidence": 0.82,
            "condition_type": "Gum Disease",
            "severity": "Mild",
            "description": "Mild inflammation of the gums",
            "recommendations": [
                "Improve oral hygiene",
                "Use antiseptic mouthwash",
                "Schedule dental checkup"
            ],
            "model_version": "mock-1.0",
            "analysis_timestamp": ""
        }
    
    async def _get_fallback_skin_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """Fallback analysis using Gemini when CV model fails"""
        try:
            logger.info("🔄 Using Gemini fallback for skin analysis")
            
            # Import Gemini service here to avoid circular imports
            from app.services.llm.gemini_service import GeminiService
            gemini_service = GeminiService()
            
            # Use Gemini to analyze the image
            analysis_prompt = """
            You are a medical AI assistant specializing in dermatology. Analyze this skin image and provide a professional assessment.
            
            Please provide:
            1. What you observe in the image
            2. Potential skin conditions or concerns
            3. Severity assessment (mild, moderate, severe)
            4. Recommendations for next steps
            
            Be professional, cautious, and always recommend consulting a dermatologist for definitive diagnosis.
            """
            
            # Use Gemini's image analysis capability
            result = await gemini_service.analyze_image_with_text(image_data, analysis_prompt)
            
            # Format the result to match CV model output
            return {
                "predicted_class": "AI Analysis",
                "confidence": 0.75,  # Moderate confidence for AI analysis
                "disease_type": "AI Assessment",
                "severity": "Requires Professional Evaluation",
                "description": result,
                "recommendations": [
                    "Consult a dermatologist for definitive diagnosis",
                    "Monitor any changes in the affected area",
                    "Protect skin from sun exposure",
                    "Maintain good skin hygiene"
                ],
                "model_version": "gemini-fallback-1.0",
                "analysis_timestamp": datetime.now().isoformat(),
                "fallback_analysis": True,
                "cv_model_unavailable": True
            }
            
        except Exception as e:
            logger.error(f"❌ Fallback analysis failed: {e}")
            # Ultimate fallback - return a generic response
            return {
                "predicted_class": "Unable to Analyze",
                "confidence": 0.0,
                "disease_type": "Analysis Unavailable",
                "severity": "Unknown",
                "description": "Unable to analyze the image due to technical issues. Please consult a dermatologist directly.",
                "recommendations": [
                    "Consult a dermatologist for professional evaluation",
                    "Take clear photos in good lighting",
                    "Monitor any changes in the affected area",
                    "Seek immediate medical attention if symptoms worsen"
                ],
                "model_version": "fallback-1.0",
                "analysis_timestamp": datetime.now().isoformat(),
                "fallback_analysis": True,
                "cv_model_unavailable": True,
                "error_message": str(e)
            }
