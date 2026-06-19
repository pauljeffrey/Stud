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

# Key prefix constants — kept short to reduce per-key byte overhead.
# Mapping: old prefix          → new prefix
#   chat_session:              → cs:
#   game_state:                → gs:
#   game_session:              → gses:
#   quiz_session:              → qses:
#   quiz_progress:             → qp:
#   doc_processing:            → dp:
#   user_session:              → uses:
#   user:profile:              → up:
#   rate_limit:{key}           → {key}  (callers already prefix with "rl:")
#   demo_game:                 → dg:    (used externally in game_v2.py)
_K_CHAT  = "cs"
_K_GS    = "gs"
_K_GSES  = "gses"
_K_QSES  = "qses"
_K_QP    = "qp"
_K_DP    = "dp"
_K_USES  = "uses"
_K_UP    = "up"


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
        ttl: int = 3600
    ) -> bool:
        """Store chat session"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        key = f"{_K_CHAT}:{user_id}:{document_id if document_id else session_id}"
        try:
            await self.client.setex(key, ttl, json.dumps(chat_history))
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
            key = f"{_K_CHAT}:{user_id}:{document_id}"
        elif session_id:
            key = f"{_K_CHAT}:{user_id}:{session_id}"
        else:
            return None
        
        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
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
            key = f"{_K_CHAT}:{user_id}:{document_id}"
        elif session_id:
            key = f"{_K_CHAT}:{user_id}:{session_id}"
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
        ttl: int = 3600
    ) -> bool:
        """Cache game state"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            await self.client.setex(
                f"{_K_GS}:{game_id}",
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
        
        try:
            data = await self.client.get(f"{_K_GS}:{game_id}")
            return json.loads(data) if data else None
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
        
        try:
            await self.client.delete(f"{_K_GS}:{game_id}")
            return True
        except Exception as e:
            logger.warning("Redis delete_game_state error: %s", e)
            return False
    
    async def get_user_active_games(self, user_id: str) -> List[str]:
        """Get list of active game IDs for user"""
        await self._ensure_connected()
        if not self.client:
            return []
        
        try:
            keys = []
            async for key in self.client.scan_iter(match=f"{_K_GS}:*"):
                game_data = await self.get_game_state(key.replace(f"{_K_GS}:", ""))
                if game_data and game_data.get("user_id") == user_id:
                    keys.append(key.replace(f"{_K_GS}:", ""))
            return keys
        except Exception as e:
            logger.warning("Redis get_user_active_games error: %s", e)
            return []
    
    # ============================================
    # COMPREHENSIVE STATE MANAGEMENT
    # Stored as a single key instead of 5 to save key overhead.
    # Internal storage uses short field names: gw, gs, cs, ns, pc
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
        """Save complete game session state to Redis as a single key."""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            payload = {
                "gw": game_world,
                "gs": game_state,
                "cs": case_state,
                "ns": npc_states,
            }
            if previous_cases is not None:
                payload["pc"] = previous_cases
            await self.client.setex(
                f"{_K_GSES}:{user_id}:{session_id}",
                ttl,
                json.dumps(payload, default=str)
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
        """Get complete game session state from Redis."""
        await self._ensure_connected()
        if not self.client:
            return None
        
        try:
            data = await self.client.get(f"{_K_GSES}:{user_id}:{session_id}")
            if not data:
                return None
            raw = json.loads(data)
            # Expand short field names back to descriptive names for callers
            return {
                "game_world":      raw["gw"],
                "game_state":      raw["gs"],
                "case_state":      raw["cs"],
                "npc_states":      raw["ns"],
                "previous_cases":  raw.get("pc"),
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
            await self.client.delete(f"{_K_GSES}:{user_id}:{session_id}")
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
        ttl: int = 1800
    ) -> bool:
        """Cache quiz session"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            await self.client.setex(
                f"{_K_QSES}:{quiz_id}",
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
        
        try:
            data = await self.client.get(f"{_K_QSES}:{quiz_id}")
            return json.loads(data) if data else None
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
        """Cache quiz progress. Stored with short field names to save memory."""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            # Short field names: a=answers, cq=current_question, tr=time_remaining, ua=updated_at
            progress = {
                "a":  answers,
                "cq": current_question,
                "tr": time_remaining,
                "ua": str(datetime.now()),
            }
            await self.client.setex(
                f"{_K_QP}:{user_id}:{quiz_id}",
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
        """Get quiz progress. Expands short field names back to descriptive names."""
        await self._ensure_connected()
        if not self.client:
            return None
        
        try:
            data = await self.client.get(f"{_K_QP}:{user_id}:{quiz_id}")
            if not data:
                return None
            raw = json.loads(data)
            return {
                "answers":          raw.get("a",  raw.get("answers")),
                "current_question": raw.get("cq", raw.get("current_question")),
                "time_remaining":   raw.get("tr", raw.get("time_remaining")),
                "updated_at":       raw.get("ua", raw.get("updated_at")),
            }
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
        ttl: int = 7200
    ) -> bool:
        """Cache document processing status. Stored with short field names."""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            # Short field names: s=status, p=progress, m=metadata, ua=updated_at
            data = {
                "s":  status,
                "p":  progress,
                "m":  metadata or {},
                "ua": str(datetime.now()),
            }
            await self.client.setex(
                f"{_K_DP}:{document_id}",
                ttl,
                json.dumps(data)
            )
            return True
        except Exception as e:
            logger.warning("Redis cache_document_processing error: %s", e)
            return False
    
    async def get_document_processing(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document processing status. Expands short field names."""
        await self._ensure_connected()
        if not self.client:
            return None
        
        try:
            data = await self.client.get(f"{_K_DP}:{document_id}")
            if not data:
                return None
            raw = json.loads(data)
            return {
                "status":     raw.get("s",  raw.get("status")),
                "progress":   raw.get("p",  raw.get("progress")),
                "metadata":   raw.get("m",  raw.get("metadata")),
                "updated_at": raw.get("ua", raw.get("updated_at")),
            }
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
        ttl: int = 86400
    ) -> bool:
        """Cache user session data"""
        await self._ensure_connected()
        if not self.client:
            return False
        
        try:
            await self.client.setex(
                f"{_K_USES}:{user_id}",
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
        
        try:
            data = await self.client.get(f"{_K_USES}:{user_id}")
            return json.loads(data) if data else None
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
        window: int
    ) -> tuple[bool, int]:
        """
        Check rate limit.
        The key is stored as-is; callers are responsible for namespacing
        (e.g. "rl:{bucket}:{ip}"). No extra prefix is added here.
        Returns (is_allowed, remaining_requests).
        """
        await self._ensure_connected()
        if not self.client:
            return True, limit
        
        try:
            current = await self.client.get(key)
            if current is None:
                await self.client.setex(key, window, 1)
                return True, limit - 1
            
            current_count = int(current)
            if current_count >= limit:
                return False, 0
            
            await self.client.incr(key)
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
