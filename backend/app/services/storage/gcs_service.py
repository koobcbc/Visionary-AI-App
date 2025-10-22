"""
Google Cloud Storage service for image management
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import logging

from google.cloud import storage
from google.cloud.exceptions import NotFound

from app.core.config import settings
from app.core.exceptions import StorageError
from app.core.logging import logger


class GCSService:
    """Manages Google Cloud Storage operations for images"""
    
    def __init__(self):
        try:
            self.client = storage.Client(project=settings.GCP_PROJECT_ID)
            self.bucket_name = settings.GCS_BUCKET_NAME
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Ensure bucket exists
            if not self.bucket.exists():
                self.bucket = self.client.create_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            
            logger.info(f"✅ Connected to GCS bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ GCS connection failed: {e}")
            raise StorageError(f"GCS connection failed: {str(e)}")
    
    async def upload_image(
        self, 
        image_data: bytes, 
        filename: str, 
        user_id: str, 
        speciality: str
    ) -> str:
        """Upload image to GCS and return public URL"""
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'png'
            unique_filename = f"{user_id}/{speciality}/{uuid.uuid4()}.{file_extension}"
            
            # Create blob
            blob = self.bucket.blob(unique_filename)
            
            # Upload with metadata
            blob.upload_from_string(
                image_data,
                content_type=f"image/{file_extension}",
                metadata={
                    "user_id": user_id,
                    "speciality": speciality,
                    "original_filename": filename,
                    "uploaded_at": datetime.utcnow().isoformat()
                }
            )
            
            # Make blob publicly readable
            blob.make_public()
            
            # Return public URL
            url = blob.public_url
            logger.info(f"📸 Image uploaded: {unique_filename}")
            return url
            
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            raise StorageError(f"Failed to upload image: {str(e)}")
    
    async def download_image(self, image_url: str) -> bytes:
        """Download image from GCS URL"""
        try:
            # Extract blob name from URL
            blob_name = image_url.split(f"{self.bucket_name}/")[-1]
            blob = self.bucket.blob(blob_name)
            
            # Download image data
            image_data = blob.download_as_bytes()
            logger.info(f"📥 Image downloaded: {blob_name}")
            return image_data
            
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            raise StorageError(f"Failed to download image: {str(e)}")
    
    async def get_image_info(self, image_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get image information and metadata"""
        try:
            # List blobs for user
            blobs = self.bucket.list_blobs(prefix=f"{user_id}/")
            
            for blob in blobs:
                if image_id in blob.name:
                    metadata = blob.metadata or {}
                    return {
                        "image_id": image_id,
                        "filename": metadata.get("original_filename", blob.name.split("/")[-1]),
                        "url": blob.public_url,
                        "speciality": metadata.get("speciality"),
                        "uploaded_at": metadata.get("uploaded_at"),
                        "size_bytes": blob.size,
                        "content_type": blob.content_type,
                        "metadata": metadata
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            raise StorageError(f"Failed to get image info: {str(e)}")
    
    async def delete_image(self, image_id: str, user_id: str) -> bool:
        """Delete image from GCS"""
        try:
            # List blobs for user
            blobs = self.bucket.list_blobs(prefix=f"{user_id}/")
            
            for blob in blobs:
                if image_id in blob.name:
                    blob.delete()
                    logger.info(f"🗑️ Image deleted: {blob.name}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            raise StorageError(f"Failed to delete image: {str(e)}")
    
    async def list_user_images(
        self, 
        user_id: str, 
        speciality: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List user's images"""
        try:
            prefix = f"{user_id}/"
            if speciality:
                prefix += f"{speciality}/"
            
            blobs = self.bucket.list_blobs(prefix=prefix)
            images = []
            
            for blob in blobs:
                if len(images) >= limit:
                    break
                
                metadata = blob.metadata or {}
                images.append({
                    "image_id": blob.name.split("/")[-1].split(".")[0],
                    "filename": metadata.get("original_filename", blob.name.split("/")[-1]),
                    "url": blob.public_url,
                    "speciality": metadata.get("speciality"),
                    "uploaded_at": metadata.get("uploaded_at"),
                    "size_bytes": blob.size,
                    "content_type": blob.content_type
                })
            
            return images
            
        except Exception as e:
            logger.error(f"Error listing images: {e}")
            raise StorageError(f"Failed to list images: {str(e)}")
    
    async def cleanup_old_images(self, days_old: int = 30) -> int:
        """Clean up old images"""
        try:
            cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            deleted_count = 0
            blobs = self.bucket.list_blobs()
            
            for blob in blobs:
                if blob.time_created < cutoff_date:
                    blob.delete()
                    deleted_count += 1
            
            logger.info(f"🧹 Cleaned up {deleted_count} old images")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up images: {e}")
            raise StorageError(f"Failed to cleanup images: {str(e)}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_size = 0
            total_count = 0
            speciality_counts = {}
            
            blobs = self.bucket.list_blobs()
            
            for blob in blobs:
                total_size += blob.size
                total_count += 1
                
                metadata = blob.metadata or {}
                speciality = metadata.get("speciality", "unknown")
                speciality_counts[speciality] = speciality_counts.get(speciality, 0) + 1
            
            return {
                "total_images": total_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "speciality_distribution": speciality_counts,
                "bucket_name": self.bucket_name
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            raise StorageError(f"Failed to get storage stats: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check GCS connectivity"""
        try:
            # Try to list blobs
            blobs = self.bucket.list_blobs(max_results=1)
            list(blobs)  # Consume the iterator
            return True
        except Exception as e:
            logger.error(f"GCS health check failed: {e}")
            return False
