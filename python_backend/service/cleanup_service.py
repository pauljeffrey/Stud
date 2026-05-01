"""
Cleanup Service for Stud
Automatically deletes expired documents and their vector indices
Runs as a background task every hour
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import os

from service.database import get_database_service
from service.s3_service import get_s3_service
from pinecone import PineconeAsyncio

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up expired documents"""
    
    def __init__(self):
        """Initialize cleanup service"""
        self.db_service = get_database_service()
        self.s3_service = get_s3_service()
        
        # Initialize Pinecone if API key available
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if pinecone_api_key:
            self.pinecone = PineconeAsyncio(api_key=pinecone_api_key)
        else:
            self.pinecone = None
            logger.warning("Pinecone API key not set - cleanup will skip Pinecone operations")
    
    async def cleanup_expired_documents(self) -> Dict[str, Any]:
        """
        Find and delete expired documents.
        Documents expire after 2 hours in vector DB (Pinecone).
        Files are kept in S3 (if enabled) for re-ingestion.
        
        This is automatically triggered every hour via background task in main.py
        """
        try:
            # Find expired documents using database service
            expired_threshold = datetime.now() - timedelta(hours=2)
            
            # Get all documents and filter expired ones
            # Note: This is a simplified approach - in production, use a query with expiration filter
            all_docs = await self.db_service.get_user_documents("", limit=1000)  # Get all docs (admin operation)
            expired_docs = [
                doc for doc in all_docs
                if doc.get("pinecone_index_expires_at") and 
                datetime.fromisoformat(doc["pinecone_index_expires_at"].replace('Z', '+00:00')) < expired_threshold
            ]
            
            deleted_count = 0
            errors = []
            
            for doc in expired_docs:
                try:
                    doc_id = doc["id"]
                    index_name = doc.get("pinecone_index_name")
                    
                    # Delete Pinecone index
                    if index_name and self.pinecone:
                        try:
                            await self.pinecone.delete_index(index_name)
                            logger.info(f"Deleted Pinecone index: {index_name}")
                        except Exception as e:
                            logger.warning(f"Error deleting Pinecone index {index_name}: {e}")
                            errors.append(f"Pinecone index {index_name}: {str(e)}")
                    
                    # Note: We don't delete from S3 - files stay there for re-ingestion
                    # Only mark as expired in database
                    await self.db_service.update_document(doc_id, {
                        "pinecone_index_name": None,
                        "pinecone_index_expires_at": None,
                        "processing_status": "expired"
                    })
                    
                    deleted_count += 1
                    logger.info(f"Cleaned up expired document: {doc_id}")
                    
                except Exception as e:
                    logger.error(f"Error cleaning up document {doc.get('id', 'unknown')}: {e}")
                    errors.append(f"Document {doc.get('id', 'unknown')}: {str(e)}")
            
            result = {
                "success": True,
                "deleted_count": deleted_count,
                "total_expired": len(expired_docs),
                "errors": errors if errors else None
            }
            
            logger.info(f"Cleanup completed: {deleted_count}/{len(expired_docs)} documents cleaned")
            return result
            
        except Exception as e:
            logger.error(f"Cleanup service error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_old_game_states(self, days: int = 7) -> Dict[str, Any]:
        """
        Clean up old game states (optional, for demo games)
        
        Args:
            days: Number of days to keep game states
            
        Returns:
            Cleanup result dictionary
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_iso = cutoff_date.isoformat()
            deleted = await self.db_service.delete_demo_game_states_older_than(cutoff_iso)
            logger.info(f"Demo game state cleanup: deleted {deleted} rows older than {cutoff_iso}")
            return {
                "success": True,
                "cutoff": cutoff_iso,
                "deleted_count": deleted,
            }
        except Exception as e:
            logger.error(f"Game state cleanup error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
_cleanup_service_instance = None


def get_cleanup_service() -> CleanupService:
    """Get cleanup service instance"""
    global _cleanup_service_instance
    if _cleanup_service_instance is None:
        _cleanup_service_instance = CleanupService()
    return _cleanup_service_instance


# Background task function
async def run_cleanup_task():
    """Background task to run cleanup periodically"""
    cleanup_service = get_cleanup_service()
    
    while True:
        try:
            await cleanup_service.cleanup_expired_documents()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error("Cleanup task error: %s", e)
            await asyncio.sleep(3600)
