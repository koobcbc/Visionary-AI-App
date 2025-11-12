# firestore_service.py
"""
Firebase Firestore + Storage Service
------------------------------------
Handles Supervisor Agent persistence:
- Store/retrieve messages
- Save Vision results
- Save final reports
- Generate signed URLs for images stored in Firebase Storage
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import firestore, storage
from google.api_core import exceptions as gcloud_exceptions

# -------------------------------------------------------
# 🔧 Firebase / Firestore Initialization
# -------------------------------------------------------
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "chats")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

if not FIREBASE_PROJECT_ID:
    raise RuntimeError("❌ FIREBASE_PROJECT_ID is missing in environment variables.")

_firestore_client: Optional[firestore.Client] = None
_storage_client: Optional[storage.Client] = None


def get_firestore() -> firestore.Client:
    """Singleton Firestore client."""
    global _firestore_client
    if not _firestore_client:
        _firestore_client = firestore.Client(project=FIREBASE_PROJECT_ID)
    return _firestore_client


def get_storage() -> storage.Client:
    """Singleton Storage client."""
    global _storage_client
    if not _storage_client:
        _storage_client = storage.Client(project=FIREBASE_PROJECT_ID)
    return _storage_client


# -------------------------------------------------------
# 🧱 Firestore Service Class
# -------------------------------------------------------
class FirestoreService:
    """Handles chat messages, reports, and image URLs."""

    def __init__(self):
        self.db = get_firestore()
        self.bucket_name = FIREBASE_STORAGE_BUCKET
        self.bucket = get_storage().bucket(self.bucket_name) if self.bucket_name else None

    # =====================================================
    # 🔹 Chat Messages
    # =====================================================
    def save_message(self, chat_id: str, message: Dict[str, Any]) -> bool:
        """
        Save a chat message (user or bot).
        Schema:
        {
            "sender": "user" | "bot",
            "user": "email",
            "userId": "Firebase UID",
            "text": "message text",
            "image": "optional URL",
            "createdAt": timestamp
        }
        """
        try:
            message["createdAt"] = firestore.SERVER_TIMESTAMP
            self.db.collection(FIRESTORE_COLLECTION).document(chat_id).collection("messages").add(message)
            return True
        except Exception as e:
            print(f"🔥 Firestore save_message error: {e}")
            return False

    def get_chat_history(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch chat history for the given chat_id.
        Returns a list of message dicts ordered by timestamp ascending.
        """
        try:
            messages_ref = (
                self.db.collection(FIRESTORE_COLLECTION)
                .document(chat_id)
                .collection("messages")
                .order_by("createdAt", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            docs = messages_ref.stream()
            return [
                {**doc.to_dict(), "id": doc.id}
                for doc in docs
            ][::-1]
        except gcloud_exceptions.NotFound:
            return []
        except Exception as e:
            print(f"🔥 Firestore get_chat_history error: {e}")
            return []

    # =====================================================
    # 🔹 Vision Agent Results
    # =====================================================
    def log_vision_result(self, chat_id: str, result: Dict[str, Any]) -> bool:
        """
        Log Vision Agent results.
        Schema:
        {
            "speciality": "skin" | "oral",
            "diagnosis": "Acne Vulgaris",
            "confidence": 0.94,
            "timestamp": timestamp
        }
        """
        try:
            data = {
                "timestamp": firestore.SERVER_TIMESTAMP,
                **result
            }
            self.db.collection(FIRESTORE_COLLECTION).document(chat_id).collection("vision").add(data)
            return True
        except Exception as e:
            print(f"🔥 Firestore log_vision_result error: {e}")
            return False

    # =====================================================
    # 🔹 Reports
    # =====================================================
    def save_report(self, chat_id: str, report_data: Dict[str, Any]) -> bool:
        """
        Save final report/diagnosis for a chat.
        Schema:
        {
            "diagnosis": { "diagnosis_name": "...", "confidence": 0.9 },
            "report_metadata": { ... },
            "timestamp": timestamp
        }
        """
        try:
            report_data["timestamp"] = firestore.SERVER_TIMESTAMP
            self.db.collection(FIRESTORE_COLLECTION).document(chat_id).collection("reports").add(report_data)
            return True
        except Exception as e:
            print(f"🔥 Firestore save_report error: {e}")
            return False

    # =====================================================
    # 🔹 Firebase Storage Signed URLs
    # =====================================================
    def get_image_download_url(self, image_path: str, expiry_seconds: int = 3600) -> Optional[str]:
        """
        Generate a signed download URL for a Firebase Storage image.

        Args:
            image_path: The path within the Firebase bucket (e.g. 'uploads/user1/image.jpg')
            expiry_seconds: How long the URL should stay valid (default 1 hour)

        Returns:
            Signed URL (str) or None
        """
        try:
            if not self.bucket:
                raise RuntimeError("Firebase Storage bucket not configured")

            blob = self.bucket.blob(image_path)
            if not blob.exists():
                print(f"⚠️ Image not found in storage: {image_path}")
                return None

            url = blob.generate_signed_url(
                expiration=expiry_seconds,
                method="GET",
                version="v4",
            )
            return url
        except Exception as e:
            print(f"🔥 Error generating signed URL: {e}")
            return None

    # =====================================================
    # 🔹 Utility: Generic Get Document
    # =====================================================
    def get_document(self, collection_path: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Fetch any single document by ID."""
        try:
            doc_ref = self.db.collection(collection_path).document(doc_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"🔥 Firestore get_document error: {e}")
            return None

    # =====================================================
    # 🔹 Health Check (useful for Supervisor startup)
    # =====================================================
    def health_check(self) -> bool:
        """Quick sanity check to ensure Firestore & Storage are reachable."""
        try:
            # Try listing top-level chat IDs
            _ = list(self.db.collection(FIRESTORE_COLLECTION).limit(1).stream())
            if self.bucket_name:
                _ = next(self.bucket.list_blobs(max_results=1), None)
            return True
        except Exception as e:
            print(f"⚠️ Firestore/Storage health check failed: {e}")
            return False