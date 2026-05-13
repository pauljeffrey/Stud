"""
Redis Service for managing sessions and cached data
Handles user chat sessions, game sessions, and other temporary data
"""
from typing import Optional, Dict, Any, List
import json
import logging
import os
import redis.asyncio as redis
from datetime import datetime, timedelta
from configs.config import config

logger = logging.getLogger(__name__)


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
        """Ensure Redis connection is established (lazy, with sized pool)."""
        if not self._initialized and config.REDIS_URL:
            try:
                max_conns = int(os.getenv("REDIS_MAX_CONNECTIONS", "200") or 200)
                self.client = await redis.from_url(
                    config.REDIS_URL,
                    decode_responses=True,
                    encoding="utf-8",
                    max_connections=max_conns,
                    health_check_interval=30,
                    socket_keepalive=True,
                )
                self._initialized = True
            except Exception as e:
                logger.warning("Redis connection failed: %s", e)
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
            logger.warning("Redis set_chat_session error: %s", e)
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
            logger.warning("Redis get_chat_session error: %s", e)
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
            logger.warning("Redis delete_chat_session error: %s", e)
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
            logger.warning("Redis cache_game_state error: %s", e)
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
            logger.warning("Redis get_game_state error: %s", e)
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
            logger.warning("Redis delete_game_state error: %s", e)
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
            logger.warning("Redis get_user_active_games error: %s", e)
            return []
    
    # ============================================
    # COMPREHENSIVE STATE MANAGEMENT
    # ============================================
    
    async def save_game_session_state(
        self,
        user_id: str,
        session_id: str,
        game_world: Dict[str, Any],
        game_state: Dict[str, Any],
        case_state: Dict[str, Any],
        npc_states: List[Dict[str, Any]],
        previous_cases: Optional[Dict[str, Any]] = None,
        ttl: int = 3600
    ) -> bool:
        """Save complete game session state to Redis"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            # Save all components with user_id and session_id keys
            base_key = f"game_session:{user_id}:{session_id}"
            
            # Save game world
            await self.client.setex(
                f"{base_key}:game_world",
                ttl,
                json.dumps(game_world, default=str)
            )
            
            # Save game state
            await self.client.setex(
                f"{base_key}:game_state",
                ttl,
                json.dumps(game_state, default=str)
            )
            
            # Save case state
            await self.client.setex(
                f"{base_key}:case_state",
                ttl,
                json.dumps(case_state, default=str)
            )
            
            # Save NPC states
            await self.client.setex(
                f"{base_key}:npc_states",
                ttl,
                json.dumps(npc_states, default=str)
            )
            
            # Save previous cases if provided
            if previous_cases:
                await self.client.setex(
                    f"{base_key}:previous_cases",
                    ttl,
                    json.dumps(previous_cases, default=str)
                )
            
            return True
        except Exception as e:
            logger.warning("Redis save_game_session_state error: %s", e)
            return False
    
    async def get_game_session_state(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get complete game session state from Redis"""
        await self._ensure_connected()
        if not self.client:
            return None
        
        try:
            base_key = f"game_session:{user_id}:{session_id}"
            
            game_world_data = await self.client.get(f"{base_key}:game_world")
            game_state_data = await self.client.get(f"{base_key}:game_state")
            case_state_data = await self.client.get(f"{base_key}:case_state")
            npc_states_data = await self.client.get(f"{base_key}:npc_states")
            previous_cases_data = await self.client.get(f"{base_key}:previous_cases")
            
            if not all([game_world_data, game_state_data, case_state_data, npc_states_data]):
                return None
            
            return {
                "game_world": json.loads(game_world_data),
                "game_state": json.loads(game_state_data),
                "case_state": json.loads(case_state_data),
                "npc_states": json.loads(npc_states_data),
                "previous_cases": json.loads(previous_cases_data) if previous_cases_data else None
            }
        except Exception as e:
            logger.warning("Redis get_game_session_state error: %s", e)
            return None
    
    async def delete_game_session_state(
        self,
        user_id: str,
        session_id: str
    ) -> bool:
        """Delete game session state from Redis"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            base_key = f"game_session:{user_id}:{session_id}"
            keys = [
                f"{base_key}:game_world",
                f"{base_key}:game_state",
                f"{base_key}:case_state",
                f"{base_key}:npc_states",
                f"{base_key}:previous_cases"
            ]
            await self.client.delete(*keys)
            return True
        except Exception as e:
            logger.warning("Redis delete_game_session_state error: %s", e)
            return False
    
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
            logger.warning("Redis cache_quiz_session error: %s", e)
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
            logger.warning("Redis get_quiz_session error: %s", e)
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
            logger.warning("Redis cache_quiz_progress error: %s", e)
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
            logger.warning("Redis get_quiz_progress error: %s", e)
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
            logger.warning("Redis cache_document_processing error: %s", e)
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
            logger.warning("Redis get_document_processing error: %s", e)
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
            logger.warning("Redis cache_user_session error: %s", e)
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
            logger.warning("Redis get_user_session error: %s", e)
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
            logger.warning("Redis check_rate_limit error: %s", e)
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
            logger.warning("Redis delete error: %s", e)
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
            logger.warning("Redis set_with_ttl error: %s", e)
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
            logger.warning("Redis get error: %s", e)
            return None


# Global instance
_redis_service: Optional[RedisService] = None


async def get_redis_service() -> RedisService:
    """Get or create global Redis service instance"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
