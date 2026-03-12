"""
Redis Service for managing sessions and cached data
Handles user chat sessions, game sessions, and other temporary data
"""
from typing import Optional, Dict, Any, List
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from config import config


class RedisService:
    """
    Redis service for caching and session management
    Uses Redis for fast access to frequently accessed data
    """
    
    def __init__(self):
        """Initialize Redis client"""
        self.client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def _ensure_connected(self):
        """Ensure Redis connection is established"""
        if not self._initialized and config.REDIS_URL:
            try:
                self.client = await redis.from_url(
                    config.REDIS_URL,
                    decode_responses=True,
                    encoding="utf-8"
                )
                self._initialized = True
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self._initialized = False
    
    # ============================================
    # USER CHAT SESSIONS
    # ============================================
    
    async def set_chat_session(
        self,
        user_id: str,
        session_id: str,
        chat_history: List[Dict[str, str]],
        document_id: Optional[str] = None,
        ttl: int = 3600  # 1 hour default
    ) -> bool:
        """Store chat session"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        key = f"chat_session:{user_id}:{session_id}"
        if document_id:
            key = f"chat_session:{user_id}:{document_id}"
        
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(chat_history)
            )
            return True
        except Exception as e:
            print(f"Redis set_chat_session error: {e}")
            return False
    
    async def get_chat_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Optional[List[Dict[str, str]]]:
        """Get chat session"""
        await self._ensure_connected()
        if not self.client:
            return None
        
        if document_id:
            key = f"chat_session:{user_id}:{document_id}"
        elif session_id:
            key = f"chat_session:{user_id}:{session_id}"
        else:
            return None
        
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get_chat_session error: {e}")
            return None
    
    async def append_chat_message(
        self,
        user_id: str,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None,
        ttl: int = 3600
    ) -> bool:
        """Append message to chat session"""
        chat_history = await self.get_chat_session(user_id, session_id, document_id) or []
        chat_history.append({"role": role, "content": content})
        return await self.set_chat_session(
            user_id,
            session_id or "default",
            chat_history,
            document_id,
            ttl
        )
    
    async def delete_chat_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> bool:
        """Delete chat session"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        if document_id:
            key = f"chat_session:{user_id}:{document_id}"
        elif session_id:
            key = f"chat_session:{user_id}:{session_id}"
        else:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete_chat_session error: {e}")
            return False
    
    # ============================================
    # GAME SESSIONS
    # ============================================
    
    async def cache_game_state(
        self,
        game_id: str,
        game_state: Dict[str, Any],
        ttl: int = 3600  # 1 hour default
    ) -> bool:
        """Cache game state"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        key = f"game_state:{game_id}"
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(game_state, default=str)
            )
            return True
        except Exception as e:
            print(f"Redis cache_game_state error: {e}")
            return False
    
    async def get_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get cached game state"""
        await self._ensure_connected()
        if not self.client:
            return None
        
        key = f"game_state:{game_id}"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get_game_state error: {e}")
            return None
    
    async def update_game_state(
        self,
        game_id: str,
        updates: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Update cached game state"""
        current_state = await self.get_game_state(game_id) or {}
        current_state.update(updates)
        return await self.cache_game_state(game_id, current_state, ttl)
    
    async def delete_game_state(self, game_id: str) -> bool:
        """Delete cached game state"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        key = f"game_state:{game_id}"
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete_game_state error: {e}")
            return False
    
    async def get_user_active_games(self, user_id: str) -> List[str]:
        """Get list of active game IDs for user"""
        await self._ensure_connected()
        if not self.client:
            return []
        
        pattern = f"game_state:*"
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                game_data = await self.get_game_state(key.replace("game_state:", ""))
                if game_data and game_data.get("user_id") == user_id:
                    keys.append(key.replace("game_state:", ""))
            return keys
        except Exception as e:
            print(f"Redis get_user_active_games error: {e}")
            return []
    
    # ============================================
    # QUIZ SESSIONS
    # ============================================
    
    async def cache_quiz_session(
        self,
        quiz_id: str,
        quiz_data: Dict[str, Any],
        ttl: int = 1800  # 30 minutes default
    ) -> bool:
        """Cache quiz session"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        key = f"quiz_session:{quiz_id}"
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(quiz_data, default=str)
            )
            return True
        except Exception as e:
            print(f"Redis cache_quiz_session error: {e}")
            return False
    
    async def get_quiz_session(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """Get cached quiz session"""
        await self._ensure_connected()
        if not self.client:
            return None
        
        key = f"quiz_session:{quiz_id}"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get_quiz_session error: {e}")
            return None
    
    async def cache_quiz_progress(
        self,
        user_id: str,
        quiz_id: str,
        answers: Dict[str, Any],
        current_question: int,
        time_remaining: int,
        ttl: int = 1800
    ) -> bool:
        """Cache quiz progress"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        key = f"quiz_progress:{user_id}:{quiz_id}"
        try:
            progress = {
                "answers": answers,
                "current_question": current_question,
                "time_remaining": time_remaining,
                "updated_at": str(datetime.now())
            }
            await self.client.setex(
                key,
                ttl,
                json.dumps(progress)
            )
            return True
        except Exception as e:
            print(f"Redis cache_quiz_progress error: {e}")
            return False
    
    async def get_quiz_progress(
        self,
        user_id: str,
        quiz_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get quiz progress"""
        await self._ensure_connected()
        if not self.client:
            return None
        
        key = f"quiz_progress:{user_id}:{quiz_id}"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get_quiz_progress error: {e}")
            return None
    
    # ============================================
    # DOCUMENT PROCESSING CACHE
    # ============================================
    
    async def cache_document_processing(
        self,
        document_id: str,
        status: str,
        progress: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: int = 7200  # 2 hours default
    ) -> bool:
        """Cache document processing status"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        key = f"doc_processing:{document_id}"
        try:
            data = {
                "status": status,
                "progress": progress,
                "metadata": metadata or {},
                "updated_at": str(datetime.now())
            }
            await self.client.setex(
                key,
                ttl,
                json.dumps(data)
            )
            return True
        except Exception as e:
            print(f"Redis cache_document_processing error: {e}")
            return False
    
    async def get_document_processing(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document processing status"""
        await self._ensure_connected()
        if not self.client:
            return None
        
        key = f"doc_processing:{document_id}"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get_document_processing error: {e}")
            return None
    
    # ============================================
    # USER SESSION CACHE
    # ============================================
    
    async def cache_user_session(
        self,
        user_id: str,
        session_data: Dict[str, Any],
        ttl: int = 86400  # 24 hours default
    ) -> bool:
        """Cache user session data"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        key = f"user_session:{user_id}"
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(session_data, default=str)
            )
            return True
        except Exception as e:
            print(f"Redis cache_user_session error: {e}")
            return False
    
    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user session"""
        await self._ensure_connected()
        if not self.client:
            return None
        
        key = f"user_session:{user_id}"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get_user_session error: {e}")
            return None
    
    # ============================================
    # RATE LIMITING
    # ============================================
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int  # seconds
    ) -> tuple[bool, int]:
        """
        Check rate limit
        Returns (is_allowed, remaining_requests)
        """
        await self._ensure_connected()
        if not self.client:
            return True, limit
        
        rate_key = f"rate_limit:{key}"
        try:
            current = await self.client.get(rate_key)
            if current is None:
                await self.client.setex(rate_key, window, 1)
                return True, limit - 1
            
            current_count = int(current)
            if current_count >= limit:
                return False, 0
            
            await self.client.incr(rate_key)
            return True, limit - current_count - 1
        except Exception as e:
            print(f"Redis check_rate_limit error: {e}")
            return True, limit
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def set_with_ttl(
        self,
        key: str,
        value: Any,
        ttl: int
    ) -> bool:
        """Set a key with TTL"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str) if not isinstance(value, str) else value
            )
            return True
        except Exception as e:
            print(f"Redis set_with_ttl error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a key"""
        await self._ensure_connected()
        if not self.client:
            return None
        
        try:
            data = await self.client.get(key)
            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None


# Global instance
_redis_service: Optional[RedisService] = None


async def get_redis_service() -> RedisService:
    """Get or create global Redis service instance"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
