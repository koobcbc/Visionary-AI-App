"""
Image validation service for medical images
"""

from typing import Tuple, Optional, Dict, Any
import io
from PIL import Image
import logging

from app.core.config import settings
from app.core.exceptions import ImageValidationError
from app.core.logging import logger
from app.services.llm.gemini_service import GeminiService


class ImageValidator:
    """Validates uploaded images for medical analysis"""
    
    def __init__(self):
        self.max_size_mb = settings.MAX_IMAGE_SIZE_MB
        self.min_dimension = settings.MIN_IMAGE_DIMENSION
        self.allowed_types = settings.ALLOWED_IMAGE_TYPES
        self.llm_service = GeminiService()
    
    async def validate_file_properties(self, file) -> bool:
        """Validate file properties (size, type)"""
        try:
            # Check file size
            if hasattr(file, 'size') and file.size:
                size_mb = file.size / (1024 * 1024)
                if size_mb > self.max_size_mb:
                    raise ImageValidationError(
                        f"File too large: {size_mb:.1f}MB (max: {self.max_size_mb}MB)"
                    )
            
            # Check content type
            if hasattr(file, 'content_type') and file.content_type:
                if file.content_type not in self.allowed_types:
                    raise ImageValidationError(
                        f"Unsupported file type: {file.content_type}. "
                        f"Allowed types: {', '.join(self.allowed_types)}"
                    )
            
            return True
            
        except ImageValidationError:
            raise
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise ImageValidationError(f"File validation failed: {str(e)}")
    
    async def validate_image_content(
        self, 
        image_data: bytes, 
        speciality: str
    ) -> Tuple[bool, str]:
        """Validate image content using AI"""
        try:
            # First validate basic image properties
            is_valid_basic, basic_reason = await self._validate_basic_properties(image_data)
            if not is_valid_basic:
                return False, basic_reason
            
            # Then validate content with AI
            is_valid_content, content_reason = await self.llm_service.validate_image_content(
                image_data=image_data,
                speciality=speciality
            )
            
            if not is_valid_content:
                return False, content_reason
            
            return True, "Image validation passed"
            
        except Exception as e:
            logger.error(f"Image content validation error: {e}")
            return False, f"Validation error: {str(e)}"
    
    async def _validate_basic_properties(self, image_data: bytes) -> Tuple[bool, str]:
        """Validate basic image properties"""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Check dimensions
            width, height = image.size
            if width < self.min_dimension or height < self.min_dimension:
                return False, f"Image too small: {width}x{height} (min: {self.min_dimension}x{self.min_dimension})"
            
            # Check if image is corrupted
            try:
                image.verify()
            except Exception:
                return False, "Image appears to be corrupted"
            
            # Check aspect ratio (prevent extremely distorted images)
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 10:  # Very wide or very tall
                return False, f"Image aspect ratio too extreme: {aspect_ratio:.1f}:1"
            
            return True, "Basic validation passed"
            
        except Exception as e:
            logger.error(f"Basic image validation error: {e}")
            return False, f"Image validation failed: {str(e)}"
    
    def validate_image_format(self, image_data: bytes) -> Tuple[bool, str]:
        """Validate image format"""
        try:
            image = Image.open(io.BytesIO(image_data))
            format_name = image.format.lower()
            
            if format_name not in ['jpeg', 'png', 'webp']:
                return False, f"Unsupported image format: {format_name}"
            
            return True, f"Valid {format_name} image"
            
        except Exception as e:
            return False, f"Invalid image format: {str(e)}"
    
    def get_image_metadata(self, image_data: bytes) -> Dict[str, Any]:
        """Extract image metadata"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "aspect_ratio": round(image.width / image.height, 2),
                "file_size_bytes": len(image_data),
                "file_size_mb": round(len(image_data) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
            return {}
    
    def suggest_image_improvements(self, image_data: bytes) -> list[str]:
        """Suggest improvements for image quality"""
        suggestions = []
        
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            # Check resolution
            if width < 512 or height < 512:
                suggestions.append("Consider using a higher resolution image for better analysis")
            
            # Check aspect ratio
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 3:
                suggestions.append("Try to capture the image with a more balanced aspect ratio")
            
            # Check file size
            size_mb = len(image_data) / (1024 * 1024)
            if size_mb < 0.1:
                suggestions.append("Image file size is very small - ensure good image quality")
            
            # Check color mode
            if image.mode == 'L':  # Grayscale
                suggestions.append("Color images may provide better analysis results")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error analyzing image for suggestions: {e}")
            return ["Unable to analyze image for suggestions"]
    
    async def validate_for_speciality(
        self, 
        image_data: bytes, 
        speciality: str
    ) -> Dict[str, Any]:
        """Comprehensive validation for specific medical speciality"""
        try:
            # Basic validation
            is_valid_basic, basic_reason = await self._validate_basic_properties(image_data)
            
            # Format validation
            is_valid_format, format_reason = self.validate_image_format(image_data)
            
            # Content validation
            is_valid_content, content_reason = await self.llm_service.validate_image_content(
                image_data=image_data,
                speciality=speciality
            )
            
            # Overall validation
            is_valid = is_valid_basic and is_valid_format and is_valid_content
            
            # Get metadata and suggestions
            metadata = self.get_image_metadata(image_data)
            suggestions = self.suggest_image_improvements(image_data)
            
            return {
                "is_valid": is_valid,
                "basic_validation": {
                    "passed": is_valid_basic,
                    "reason": basic_reason
                },
                "format_validation": {
                    "passed": is_valid_format,
                    "reason": format_reason
                },
                "content_validation": {
                    "passed": is_valid_content,
                    "reason": content_reason
                },
                "metadata": metadata,
                "suggestions": suggestions,
                "speciality": speciality
            }
            
        except Exception as e:
            logger.error(f"Speciality validation error: {e}")
            return {
                "is_valid": False,
                "error": str(e),
                "speciality": speciality
            }
