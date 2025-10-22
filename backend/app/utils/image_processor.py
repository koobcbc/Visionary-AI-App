"""
Image processing utilities
"""

import io
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import logging

from app.core.logging import logger


class ImageProcessor:
    """Image processing utilities for medical images"""
    
    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'WEBP']
        self.max_dimensions = (4096, 4096)
        self.min_dimensions = (224, 224)
    
    def process_image(self, image_data: bytes, processing_options: Dict[str, Any] = None) -> bytes:
        """Process image with specified options"""
        try:
            # Default processing options
            options = {
                'resize': True,
                'enhance': True,
                'normalize': True,
                'target_size': (512, 512),
                'quality': 95
            }
            
            if processing_options:
                options.update(processing_options)
            
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if requested
            if options.get('resize', True):
                image = self._resize_image(image, options.get('target_size', (512, 512)))
            
            # Enhance if requested
            if options.get('enhance', True):
                image = self._enhance_image(image)
            
            # Normalize if requested
            if options.get('normalize', True):
                image = self._normalize_image(image)
            
            # Save processed image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=options.get('quality', 95))
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            raise
    
    def _resize_image(self, image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        try:
            # Calculate new size maintaining aspect ratio
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Create new image with target size and paste resized image
            new_image = Image.new('RGB', target_size, (255, 255, 255))
            new_image.paste(image, ((target_size[0] - image.width) // 2, 
                                  (target_size[1] - image.height) // 2))
            
            return new_image
            
        except Exception as e:
            logger.error(f"Image resize error: {e}")
            return image
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality"""
        try:
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Enhance brightness slightly
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.05)
            
            return image
            
        except Exception as e:
            logger.error(f"Image enhancement error: {e}")
            return image
    
    def _normalize_image(self, image: Image.Image) -> Image.Image:
        """Normalize image for better analysis"""
        try:
            # Convert to numpy array
            img_array = np.array(image)
            
            # Normalize to 0-1 range
            img_normalized = img_array.astype(np.float32) / 255.0
            
            # Apply histogram equalization
            img_normalized = self._histogram_equalization(img_normalized)
            
            # Convert back to PIL Image
            img_normalized = (img_normalized * 255).astype(np.uint8)
            return Image.fromarray(img_normalized)
            
        except Exception as e:
            logger.error(f"Image normalization error: {e}")
            return image
    
    def _histogram_equalization(self, img: np.ndarray) -> np.ndarray:
        """Apply histogram equalization"""
        try:
            # Convert to grayscale for histogram equalization
            if len(img.shape) == 3:
                gray = np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])
            else:
                gray = img
            
            # Calculate histogram
            hist, bins = np.histogram(gray.flatten(), 256, [0, 1])
            
            # Calculate cumulative distribution function
            cdf = hist.cumsum()
            cdf_normalized = cdf / cdf[-1]
            
            # Apply histogram equalization
            img_equalized = np.interp(gray.flatten(), bins[:-1], cdf_normalized)
            img_equalized = img_equalized.reshape(gray.shape)
            
            # Apply to color channels
            if len(img.shape) == 3:
                result = img.copy()
                for i in range(3):
                    result[..., i] = img_equalized
                return result
            else:
                return img_equalized
                
        except Exception as e:
            logger.error(f"Histogram equalization error: {e}")
            return img
    
    def get_image_metadata(self, image_data: bytes) -> Dict[str, Any]:
        """Get comprehensive image metadata"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            metadata = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height,
                'aspect_ratio': round(image.width / image.height, 2),
                'file_size_bytes': len(image_data),
                'file_size_mb': round(len(image_data) / (1024 * 1024), 2),
                'has_transparency': image.mode in ('RGBA', 'LA', 'P'),
                'color_count': len(image.getcolors(maxcolors=256*256*256)) if image.mode == 'P' else None
            }
            
            # Add EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                metadata['exif'] = self._extract_exif_data(image._getexif())
            
            return metadata
            
        except Exception as e:
            logger.error(f"Image metadata extraction error: {e}")
            return {}
    
    def _extract_exif_data(self, exif_data) -> Dict[str, Any]:
        """Extract relevant EXIF data"""
        try:
            exif_info = {}
            
            # Common EXIF tags
            exif_tags = {
                271: 'make',
                272: 'model',
                274: 'orientation',
                282: 'x_resolution',
                283: 'y_resolution',
                306: 'datetime',
                36867: 'datetime_original',
                36868: 'datetime_digitized'
            }
            
            for tag_id, tag_name in exif_tags.items():
                if tag_id in exif_data:
                    exif_info[tag_name] = exif_data[tag_id]
            
            return exif_info
            
        except Exception as e:
            logger.error(f"EXIF data extraction error: {e}")
            return {}
    
    def validate_image_for_medical_analysis(self, image_data: bytes) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate image suitability for medical analysis"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Check dimensions
            width, height = image.size
            if width < self.min_dimensions[0] or height < self.min_dimensions[1]:
                return False, f"Image too small: {width}x{height}", {}
            
            if width > self.max_dimensions[0] or height > self.max_dimensions[1]:
                return False, f"Image too large: {width}x{height}", {}
            
            # Check format
            if image.format not in self.supported_formats:
                return False, f"Unsupported format: {image.format}", {}
            
            # Check aspect ratio
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 10:
                return False, f"Extreme aspect ratio: {aspect_ratio:.1f}:1", {}
            
            # Check image quality
            quality_score = self._calculate_image_quality(image)
            
            validation_info = {
                'dimensions': (width, height),
                'format': image.format,
                'aspect_ratio': aspect_ratio,
                'quality_score': quality_score,
                'suitable_for_analysis': quality_score > 0.5
            }
            
            if quality_score <= 0.5:
                return False, f"Poor image quality: {quality_score:.2f}", validation_info
            
            return True, "Image suitable for medical analysis", validation_info
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False, f"Image validation error: {str(e)}", {}
    
    def _calculate_image_quality(self, image: Image.Image) -> float:
        """Calculate image quality score"""
        try:
            # Convert to grayscale for analysis
            if image.mode != 'L':
                gray_image = image.convert('L')
            else:
                gray_image = image
            
            # Calculate sharpness using Laplacian variance
            img_array = np.array(gray_image)
            laplacian_var = np.var(np.gradient(np.gradient(img_array, axis=0), axis=0))
            
            # Calculate brightness
            mean_brightness = np.mean(img_array)
            
            # Calculate contrast
            contrast = np.std(img_array)
            
            # Normalize scores
            sharpness_score = min(laplacian_var / 1000, 1.0)
            brightness_score = 1.0 - abs(mean_brightness - 128) / 128
            contrast_score = min(contrast / 64, 1.0)
            
            # Overall quality score
            quality_score = (sharpness_score + brightness_score + contrast_score) / 3
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Image quality calculation error: {e}")
            return 0.0
    
    def create_thumbnail(self, image_data: bytes, size: Tuple[int, int] = (150, 150)) -> bytes:
        """Create thumbnail of image"""
        try:
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Thumbnail creation error: {e}")
            raise
    
    def convert_format(self, image_data: bytes, target_format: str = 'JPEG') -> bytes:
        """Convert image to target format"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if target is JPEG
            if target_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            output = io.BytesIO()
            image.save(output, format=target_format, quality=95)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            raise
