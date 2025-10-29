"""
Image safety guardrails for medical image validation
"""

import io
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import logging

from app.core.exceptions import ImageValidationError, MedicalSafetyError
from app.core.logging import logger


class ImageGuardrails:
    """Image safety and validation guardrails"""
    
    # Minimum and maximum dimensions for medical images
    MIN_DIMENSIONS = (224, 224)
    MAX_DIMENSIONS = (4096, 4096)
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Allowed image formats
    ALLOWED_FORMATS = ['JPEG', 'PNG', 'WEBP']
    
    def __init__(self):
        pass
    
    def validate_image_safety(self, image_data: bytes) -> Tuple[bool, str, Dict[str, Any]]:
        """Comprehensive image safety validation"""
        try:
            # Basic file validation
            is_valid_basic, basic_reason = self._validate_basic_properties(image_data)
            if not is_valid_basic:
                return False, basic_reason, {}
            
            # Content validation
            is_valid_content, content_reason, content_metadata = self._validate_image_content(image_data)
            if not is_valid_content:
                return False, content_reason, content_metadata
            
            # Medical relevance validation
            is_valid_medical, medical_reason = self._validate_medical_relevance(image_data)
            if not is_valid_medical:
                return False, medical_reason, {}
            
            return True, "Image safety validated", {
                "file_size": len(image_data),
                "dimensions": content_metadata.get("dimensions"),
                "format": content_metadata.get("format")
            }
            
        except Exception as e:
            logger.error(f"Image safety validation error: {e}")
            return False, f"Image safety validation error: {str(e)}", {}
    
    def _validate_basic_properties(self, image_data: bytes) -> Tuple[bool, str]:
        """Validate basic image properties"""
        try:
            # Check file size
            if len(image_data) > self.MAX_FILE_SIZE:
                return False, f"File too large: {len(image_data) / (1024*1024):.1f}MB (max: {self.MAX_FILE_SIZE / (1024*1024):.1f}MB)"
            
            if len(image_data) < 1024:  # Less than 1KB
                return False, "File too small: may be corrupted"
            
            # Try to open image
            try:
                image = Image.open(io.BytesIO(image_data))
                image.verify()  # Verify image integrity
            except Exception as e:
                return False, f"Invalid or corrupted image: {str(e)}"
            
            return True, "Basic properties validated"
            
        except Exception as e:
            logger.error(f"Basic properties validation error: {e}")
            return False, f"Basic properties validation error: {str(e)}"
    
    def _validate_image_content(self, image_data: bytes) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate image content and format"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Check format
            if image.format not in self.ALLOWED_FORMATS:
                return False, f"Unsupported format: {image.format}", {}
            
            # Check dimensions
            width, height = image.size
            if width < self.MIN_DIMENSIONS[0] or height < self.MIN_DIMENSIONS[1]:
                return False, f"Image too small: {width}x{height} (min: {self.MIN_DIMENSIONS[0]}x{self.MIN_DIMENSIONS[1]})", {}
            
            if width > self.MAX_DIMENSIONS[0] or height > self.MAX_DIMENSIONS[1]:
                return False, f"Image too large: {width}x{height} (max: {self.MAX_DIMENSIONS[0]}x{self.MAX_DIMENSIONS[1]})", {}
            
            # Check aspect ratio
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 10:  # Very wide or very tall
                return False, f"Extreme aspect ratio: {aspect_ratio:.1f}:1", {}
            
            # Check if image is mostly empty/blank
            if self._is_image_mostly_empty(image):
                return False, "Image appears to be mostly empty or blank", {}
            
            metadata = {
                "dimensions": (width, height),
                "format": image.format,
                "mode": image.mode,
                "aspect_ratio": aspect_ratio
            }
            
            return True, "Content validated", metadata
            
        except Exception as e:
            logger.error(f"Content validation error: {e}")
            return False, f"Content validation error: {str(e)}", {}
    
    def _validate_medical_relevance(self, image_data: bytes) -> Tuple[bool, str]:
        """Validate if image is relevant for medical analysis"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Check image characteristics that might indicate medical relevance
            width, height = image.size
            
            # Check for reasonable medical image proportions
            if width < 300 or height < 300:
                return False, "Image resolution too low for medical analysis"
            
            # Check color distribution (medical images often have specific color patterns)
            if image.mode == 'RGB':
                # Analyze color distribution
                color_distribution = self._analyze_color_distribution(image)
                if color_distribution.get('is_suspicious', False):
                    return False, "Image color distribution suggests non-medical content"
            
            # Check for text overlays (might indicate screenshots or documents)
            if self._has_text_overlay(image):
                return False, "Image appears to contain text overlays"
            
            return True, "Medical relevance validated"
            
        except Exception as e:
            logger.error(f"Medical relevance validation error: {e}")
            return False, f"Medical relevance validation error: {str(e)}"
    
    def _is_image_mostly_empty(self, image: Image.Image) -> bool:
        """Check if image is mostly empty or blank"""
        try:
            # Convert to grayscale for analysis
            if image.mode != 'L':
                image = image.convert('L')
            
            # Get pixel data
            pixels = list(image.getdata())
            
            # Count very bright pixels (likely empty space)
            bright_pixels = sum(1 for pixel in pixels if pixel > 240)
            total_pixels = len(pixels)
            
            # If more than 80% of pixels are very bright, consider it mostly empty
            return (bright_pixels / total_pixels) > 0.8
            
        except Exception as e:
            logger.error(f"Empty image check error: {e}")
            return False
    
    def _analyze_color_distribution(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze color distribution for suspicious patterns"""
        try:
            # Get color histogram
            histogram = image.histogram()
            
            # Analyze RGB channels
            r_hist = histogram[0:256]
            g_hist = histogram[256:512]
            b_hist = histogram[512:768]
            
            # Check for unusual color patterns
            r_peak = max(r_hist)
            g_peak = max(g_hist)
            b_peak = max(b_hist)
            
            # If one color channel dominates significantly, it might be suspicious
            total_peak = r_peak + g_peak + b_peak
            if total_peak > 0:
                r_ratio = r_peak / total_peak
                g_ratio = g_peak / total_peak
                b_ratio = b_peak / total_peak
                
                # If any single color dominates more than 70%, it's suspicious
                is_suspicious = max(r_ratio, g_ratio, b_ratio) > 0.7
            
            return {
                "is_suspicious": is_suspicious,
                "color_distribution": {
                    "red_ratio": r_ratio if total_peak > 0 else 0,
                    "green_ratio": g_ratio if total_peak > 0 else 0,
                    "blue_ratio": b_ratio if total_peak > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Color distribution analysis error: {e}")
            return {"is_suspicious": False}
    
    def _has_text_overlay(self, image: Image.Image) -> bool:
        """Check if image has text overlays (simple heuristic)"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Look for sharp edges that might indicate text
            # This is a simple heuristic - in production, you might use OCR
            pixels = list(image.getdata())
            width, height = image.size
            
            # Count sharp transitions (potential text edges)
            sharp_transitions = 0
            for y in range(height - 1):
                for x in range(width - 1):
                    current = pixels[y * width + x]
                    right = pixels[y * width + x + 1]
                    below = pixels[(y + 1) * width + x]
                    
                    # Check for sharp transitions
                    if abs(current - right) > 100 or abs(current - below) > 100:
                        sharp_transitions += 1
            
            # If there are many sharp transitions, it might have text
            total_pixels = width * height
            transition_ratio = sharp_transitions / total_pixels
            
            return transition_ratio > 0.1  # More than 10% sharp transitions
            
        except Exception as e:
            logger.error(f"Text overlay check error: {e}")
            return False
    
    def get_image_quality_score(self, image_data: bytes) -> Dict[str, Any]:
        """Calculate image quality score for medical analysis"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            quality_metrics = {
                "resolution_score": self._calculate_resolution_score(image),
                "sharpness_score": self._calculate_sharpness_score(image),
                "lighting_score": self._calculate_lighting_score(image),
                "composition_score": self._calculate_composition_score(image)
            }
            
            # Overall quality score
            overall_score = sum(quality_metrics.values()) / len(quality_metrics)
            quality_metrics["overall_score"] = overall_score
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Quality score calculation error: {e}")
            return {"overall_score": 0.0}
    
    def _calculate_resolution_score(self, image: Image.Image) -> float:
        """Calculate resolution quality score"""
        width, height = image.size
        total_pixels = width * height
        
        # Score based on total pixel count
        if total_pixels >= 1000000:  # 1MP+
            return 1.0
        elif total_pixels >= 500000:  # 0.5MP+
            return 0.8
        elif total_pixels >= 100000:  # 0.1MP+
            return 0.6
        else:
            return 0.3
    
    def _calculate_sharpness_score(self, image: Image.Image) -> float:
        """Calculate sharpness quality score"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Simple sharpness calculation using Laplacian variance
            import numpy as np
            img_array = np.array(image)
            
            # Calculate Laplacian variance
            laplacian_var = np.var(np.gradient(np.gradient(img_array, axis=0), axis=0))
            
            # Normalize score
            if laplacian_var > 1000:
                return 1.0
            elif laplacian_var > 500:
                return 0.8
            elif laplacian_var > 100:
                return 0.6
            else:
                return 0.3
                
        except Exception:
            return 0.5  # Default score if calculation fails
    
    def _calculate_lighting_score(self, image: Image.Image) -> float:
        """Calculate lighting quality score"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            pixels = list(image.getdata())
            mean_brightness = sum(pixels) / len(pixels)
            
            # Ideal brightness range for medical images
            if 80 <= mean_brightness <= 180:
                return 1.0
            elif 60 <= mean_brightness <= 200:
                return 0.8
            elif 40 <= mean_brightness <= 220:
                return 0.6
            else:
                return 0.3
                
        except Exception:
            return 0.5
    
    def _calculate_composition_score(self, image: Image.Image) -> float:
        """Calculate composition quality score"""
        try:
            width, height = image.size
            aspect_ratio = max(width, height) / min(width, height)
            
            # Score based on aspect ratio
            if aspect_ratio <= 2.0:
                return 1.0
            elif aspect_ratio <= 3.0:
                return 0.8
            elif aspect_ratio <= 5.0:
                return 0.6
            else:
                return 0.3
                
        except Exception:
            return 0.5
