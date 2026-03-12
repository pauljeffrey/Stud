"""
Cleanup Service for Stud
Automatically deletes expired documents and their vector indices
"""
import asyncio
from datetime import datetime, timedelta
from typing import List
from supabase import create_client, Client
from pinecone import PineconeAsyncio
import os

from config import config


class CleanupService:
    """Service for cleaning up expired documents"""
    
    def __init__(self):
        """Initialize cleanup service"""
        self.supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_ROLE_KEY
        )
        
        # Initialize Pinecone if API key available
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if pinecone_api_key:
            self.pinecone = PineconeAsyncio(api_key=pinecone_api_key)
        else:
            self.pinecone = None
    
    async def cleanup_expired_documents(self):
        """
        Find and delete expired documents
        Should be run periodically (e.g., every hour)
        """
        try:
            # Find expired documents
            expired_threshold = datetime.now() - timedelta(hours=2)
            
            result = self.supabase.table("documents").select("*").lt(
                "pinecone_index_expires_at",
                expired_threshold.isoformat()
            ).execute()
            
            expired_docs = result.data if result.data else []
            
            deleted_count = 0
            for doc in expired_docs:
                try:
                    # Delete Pinecone index
                    index_name = doc.get("pinecone_index_name")
                    if index_name and self.pinecone:
                        try:
                            await self.pinecone.delete_index(index_name)
                        except Exception as e:
                            print(f"Error deleting Pinecone index {index_name}: {str(e)}")
                    
                    # Delete from Supabase
                    self.supabase.table("documents").delete().eq("id", doc["id"]).execute()
                    deleted_count += 1
                    
                except Exception as e:
                    print(f"Error deleting document {doc['id']}: {str(e)}")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "total_expired": len(expired_docs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_old_game_states(self, days: int = 7):
        """
        Clean up old game states (optional, for demo games)
        
        Args:
            days: Number of days to keep game states
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Delete old demo games
            result = self.supabase.table("game_states").delete().eq(
                "is_demo", True
            ).lt("created_at", cutoff_date.isoformat()).execute()
            
            return {
                "success": True,
                "deleted_count": len(result.data) if result.data else 0
            }
            
        except Exception as e:
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
            print(f"Cleanup task error: {str(e)}")
            await asyncio.sleep(3600)
