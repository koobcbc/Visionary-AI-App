"""
Firestore service for database operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from google.cloud import firestore
from google.cloud.firestore import ArrayUnion

from app.core.config import settings
from app.core.exceptions import StorageError, SessionExpiredError
from app.core.logging import logger
from app.models.database import ChatDocument, UserDocument, ReportDocument
from app.models.enums import ChatStatus


class FirestoreService:
    """Manages Firestore operations with session caching"""
    
    def __init__(self):
        try:
            self.db = firestore.Client(project=settings.GCP_PROJECT_ID)
            self.chats_collection = self.db.collection(settings.FIRESTORE_COLLECTION_CHATS)
            self.users_collection = self.db.collection(settings.FIRESTORE_COLLECTION_USERS)
            self.reports_collection = self.db.collection(settings.FIRESTORE_COLLECTION_REPORTS)
            
            # In-memory cache for active sessions
            self.session_cache = {}
            self.cache_timestamps = {}
            
            logger.info("✅ Connected to Firestore")
        except Exception as e:
            logger.error(f"❌ Firestore connection failed: {e}")
            raise StorageError(f"Firestore connection failed: {str(e)}")
    
    async def get_or_create_chat(
        self, 
        chat_id: str, 
        user_id: str, 
        speciality: str
    ) -> Dict[str, Any]:
        """Get chat from cache or Firestore, create if doesn't exist"""
        try:
            # Check cache first
            if chat_id in self.session_cache:
                cache_time = self.cache_timestamps.get(chat_id)
                if cache_time and (datetime.now() - cache_time).seconds < 3600:  # 1 hour cache
                    logger.info(f"📦 Cache hit for chat_id: {chat_id}")
                    return self.session_cache[chat_id]
            
            # Fetch from Firestore
            doc_ref = self.chats_collection.document(chat_id)
            doc = doc_ref.get()
            
            if doc.exists:
                chat_data = doc.to_dict()
                # Get messages from sub-collection
                messages = await self._get_chat_messages(chat_id)
                chat_data["messages"] = messages
                logger.info(f"📥 Fetched chat from Firestore: {chat_id}")
            else:
                # Create new chat with your actual schema
                chat_data = {
                    "createdAt": datetime.now(),
                    "last_message_at": datetime.now(),
                    "title": f"{speciality.title()} Consultation",
                    "updatedAt": datetime.now(),
                    "userId": user_id,
                    "speciality": speciality,
                    "metadata": {
                        "age": None,
                        "gender": None,
                        "symptoms": [],
                        "medical_history": {}
                    },
                    "image_analyzed": False,
                    "cv_result": None,
                    "status": ChatStatus.ACTIVE.value
                }
                doc_ref.set(chat_data)
                logger.info(f"✨ Created new chat: {chat_id}")
            
            # Update cache
            self.session_cache[chat_id] = chat_data
            self.cache_timestamps[chat_id] = datetime.now()
            
            return chat_data
            
        except Exception as e:
            logger.error(f"Error getting/creating chat: {e}")
            raise StorageError(f"Failed to get/create chat: {str(e)}")
    
    async def get_chat_by_id(self, chat_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get chat by ID"""
        try:
            doc_ref = self.chats_collection.document(chat_id)
            doc = doc_ref.get()
            
            if doc.exists:
                chat_data = doc.to_dict()
                # Verify user ownership
                if chat_data.get("user_id") != user_id:
                    return None
                return chat_data
            return None
            
        except Exception as e:
            logger.error(f"Error getting chat by ID: {e}")
            raise StorageError(f"Failed to get chat: {str(e)}")
    
    async def add_message(
        self, 
        chat_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add message to chat history as sub-collection"""
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now(),
                "metadata": metadata or {}
            }
            
            # Add message to messages sub-collection
            messages_ref = self.chats_collection.document(chat_id).collection("messages")
            messages_ref.add(message)
            
            # Update chat document with last_message_at
            doc_ref = self.chats_collection.document(chat_id)
            doc_ref.update({
                "last_message_at": datetime.now(),
                "updatedAt": datetime.now()
            })
            
            # Update cache
            if chat_id in self.session_cache:
                if "messages" not in self.session_cache[chat_id]:
                    self.session_cache[chat_id]["messages"] = []
                self.session_cache[chat_id]["messages"].append(message)
                self.session_cache[chat_id]["last_message_at"] = datetime.now()
                self.session_cache[chat_id]["updatedAt"] = datetime.now()
            
            logger.info(f"💬 Message added to chat: {chat_id}")
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise StorageError(f"Failed to add message: {str(e)}")
    
    async def update_metadata(self, chat_id: str, metadata: Dict[str, Any]):
        """Update chat metadata"""
        try:
            doc_ref = self.chats_collection.document(chat_id)
            doc_ref.update({
                "metadata": metadata,
                "updated_at": datetime.now().isoformat()
            })
            
            # Update cache
            if chat_id in self.session_cache:
                if "metadata" not in self.session_cache[chat_id]:
                    self.session_cache[chat_id]["metadata"] = {}
                self.session_cache[chat_id]["metadata"].update(metadata)
            
            logger.info(f"📝 Metadata updated for chat: {chat_id}")
            
        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
            raise StorageError(f"Failed to update metadata: {str(e)}")
    
    async def save_cv_result(self, chat_id: str, cv_result: Dict[str, Any]):
        """Save CV model result"""
        try:
            doc_ref = self.chats_collection.document(chat_id)
            doc_ref.update({
                "cv_result": cv_result,
                "image_analyzed": True,
                "updated_at": datetime.now().isoformat()
            })
            
            # Update cache
            if chat_id in self.session_cache:
                self.session_cache[chat_id]["cv_result"] = cv_result
                self.session_cache[chat_id]["image_analyzed"] = True
            
            logger.info(f"🔬 CV result saved for chat: {chat_id}")
            
        except Exception as e:
            logger.error(f"Error saving CV result: {e}")
            raise StorageError(f"Failed to save CV result: {str(e)}")
    
    async def save_report(
        self, 
        chat_id: str, 
        user_id: str, 
        report: Dict[str, Any]
    ) -> str:
        """Save final diagnostic report"""
        try:
            report_id = f"report_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            report_data = {
                "report_id": report_id,
                "chat_id": chat_id,
                "user_id": user_id,
                "report": report,
                "disease_type": report.get("disease_type"),
                "confidence": report.get("confidence"),
                "follow_up_required": report.get("follow_up_required") == "Yes",
                "created_at": datetime.now().isoformat()
            }
            
            self.reports_collection.document(report_id).set(report_data)
            
            # Mark chat as completed
            doc_ref = self.chats_collection.document(chat_id)
            doc_ref.update({
                "status": ChatStatus.COMPLETED.value,
                "updated_at": datetime.now().isoformat()
            })
            
            logger.info(f"📊 Report saved for chat: {chat_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise StorageError(f"Failed to save report: {str(e)}")
    
    async def get_report_by_id(self, report_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID"""
        try:
            doc_ref = self.reports_collection.document(report_id)
            doc = doc_ref.get()
            
            if doc.exists:
                report_data = doc.to_dict()
                # Verify user ownership
                if report_data.get("user_id") != user_id:
                    return None
                return report_data
            return None
            
        except Exception as e:
            logger.error(f"Error getting report: {e}")
            raise StorageError(f"Failed to get report: {str(e)}")
    
    async def list_user_reports(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List user's reports with pagination"""
        try:
            query = self.reports_collection.where("user_id", "==", user_id)
            
            if status:
                query = query.where("status", "==", status)
            
            query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
            query = query.offset(offset).limit(limit)
            
            docs = query.stream()
            reports = [doc.to_dict() for doc in docs]
            
            return reports
            
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            raise StorageError(f"Failed to list reports: {str(e)}")
    
    async def count_user_reports(self, user_id: str, status: Optional[str] = None) -> int:
        """Count user's reports"""
        try:
            query = self.reports_collection.where("user_id", "==", user_id)
            
            if status:
                query = query.where("status", "==", status)
            
            docs = query.stream()
            return len(list(docs))
            
        except Exception as e:
            logger.error(f"Error counting reports: {e}")
            raise StorageError(f"Failed to count reports: {str(e)}")
    
    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        try:
            doc_ref = self.chats_collection.document(chat_id)
            doc = doc_ref.get()
            
            if doc.exists:
                chat_data = doc.to_dict()
                if chat_data.get("user_id") == user_id:
                    doc_ref.delete()
                    self.clear_cache(chat_id)
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            raise StorageError(f"Failed to delete chat: {str(e)}")
    
    async def delete_report(self, report_id: str, user_id: str) -> bool:
        """Delete a report"""
        try:
            doc_ref = self.reports_collection.document(report_id)
            doc = doc_ref.get()
            
            if doc.exists:
                report_data = doc.to_dict()
                if report_data.get("user_id") == user_id:
                    doc_ref.delete()
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting report: {e}")
            raise StorageError(f"Failed to delete report: {str(e)}")
    
    def is_session_expired(self, chat_data: Dict[str, Any]) -> bool:
        """Check if session has expired - disabled for testing"""
        # For capstone testing, we'll disable session expiry
        return False
        
        # Original logic (commented out for testing):
        # try:
        #     expires_at = datetime.fromisoformat(chat_data.get("expires_at"))
        #     return datetime.now() > expires_at
        # except Exception:
        #     return True
    
    async def _get_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get messages from chat sub-collection"""
        try:
            messages_ref = self.chats_collection.document(chat_id).collection("messages")
            docs = messages_ref.order_by("timestamp").stream()
            
            messages = []
            for doc in docs:
                message_data = doc.to_dict()
                message_data["message_id"] = doc.id
                messages.append(message_data)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting chat messages: {e}")
            return []
    
    def clear_cache(self, chat_id: Optional[str] = None):
        """Clear session cache"""
        if chat_id:
            self.session_cache.pop(chat_id, None)
            self.cache_timestamps.pop(chat_id, None)
        else:
            self.session_cache.clear()
            self.cache_timestamps.clear()
    
    async def health_check(self) -> bool:
        """Check Firestore connectivity"""
        try:
            # Try to read from a collection
            docs = self.chats_collection.limit(1).stream()
            list(docs)  # Consume the iterator
            return True
        except Exception as e:
            logger.error(f"Firestore health check failed: {e}")
            return False
