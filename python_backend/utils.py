import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
)
from pydantic_core import to_jsonable_python

from configs.config import config


# Model overload / rate limit detection for user-friendly error messages
_MODEL_OVERLOAD_CODES = (429, 502, 503, 504)
_MODEL_OVERLOAD_PHRASES = ("503", "429", "502", "504", "UNAVAILABLE", "high demand", "rate limit", "too many requests")


def is_model_overload_error(exc: BaseException) -> bool:
    """True if the exception indicates model overload (503, 429, etc.)."""
    try:
        import httpx
        if isinstance(exc, httpx.HTTPStatusError):
            return getattr(exc.response, "status_code", None) in _MODEL_OVERLOAD_CODES
    except ImportError:
        pass
    err_str = str(exc).lower()
    if any(p.lower() in err_str for p in _MODEL_OVERLOAD_PHRASES):
        return True
    cause = getattr(exc, "__cause__", None)
    return cause is not None and is_model_overload_error(cause)


def get_user_friendly_error_message(exc: BaseException) -> str:
    """Return user-friendly message based on error type."""
    if is_model_overload_error(exc):
        return "There are too many requests at the moment. Please try again shortly."
    return "I'm sorry, I'm experiencing technical difficulties. Please try again in a moment."


def count_words_in_messages(messages: list[ModelMessage]) -> int:
    """Count total words in messages"""
    total = 0
    for msg in messages:
        if hasattr(msg, 'parts') and msg.parts:
            for part in msg.parts:
                if hasattr(part, 'content'):
                    total += len(part.content.split())
        elif isinstance(msg, dict):
            content = msg.get("content") or msg.get("message") or (msg.get("parts", [{}])[0].get("content") if msg.get("parts") else "")
            total += len(content.split())
    return total


def get_last_n_messages_by_word_count(
    messages: list[ModelMessage],
    keep_last_n: int = 10,
    max_words: int = 3000
) -> tuple[list[ModelMessage], list[ModelMessage]]:
    """
    Split messages into those to keep and those to summarize.
    Keeps last N messages, summarizes the rest if they exceed max_words.
    """
    if len(messages) <= keep_last_n:
        return messages, []
    
    messages_to_keep = messages[-keep_last_n:]
    messages_to_summarize = messages[:-keep_last_n]
    
    words_to_summarize = count_words_in_messages(messages_to_summarize)
    if words_to_summarize <= max_words:
        return messages, []
    
    return messages_to_keep, messages_to_summarize


def _messages_plain_excerpt(messages: list[ModelMessage], max_chars: int = 100_000) -> str:
    lines: List[str] = []
    for msg in messages:
        label = "assistant" if isinstance(msg, ModelResponse) else "user"
        for part in getattr(msg, "parts", None) or []:
            content = getattr(part, "content", None)
            if content:
                lines.append(f"{label}: {content}")
    return "\n".join(lines)[:max_chars]


async def _llm_summarize_excerpt(text: str) -> str:
    from model import select_model
    from pydantic_ai import Agent

    name = (
        getattr(config, "SUMMARY_MODEL_NAME", None)
        or getattr(config, "QUIZ_MODEL_NAME", None)
        or "gemini-2.0-flash"
    )
    key = (
        getattr(config, "API_KEY", None)
        or getattr(config, "GOOGLE_API_KEY", None)
        or getattr(config, "OPENAI_API_KEY", None)
        or ""
    )
    model, _ = select_model(name, key)
    agent = Agent(
        model,
        system_prompt="Summarize the prior dialogue for memory: key facts, decisions, and open questions. Max ~200 words, plain text.",
        output_type=str,
    )
    result = await agent.run(text)
    out = getattr(result, "output", None) or str(result)
    return (out or "").strip() or "[summary unavailable]"


async def summarize_old_messages(
    messages: list[ModelMessage], 
    summarize_all=False, 
    max_words: int = 3000,
    keep_last_n: int = 10
) -> list[ModelMessage]:
    """
    Summarize old messages when word count exceeds thresholds.
    Prepends one assistant summary message and keeps the recent tail.
    """
    if not messages:
        return messages

    total_words = count_words_in_messages(messages)

    if summarize_all:
        if total_words <= 1500:
            return messages
        to_keep = messages[-5:]
        to_sum = messages[:-5]
        if not to_sum:
            return messages
        try:
            excerpt = _messages_plain_excerpt(to_sum)
            summary = await _llm_summarize_excerpt(excerpt)
            summary_msg = ModelResponse(parts=[TextPart(content=f"[Earlier conversation summary]\n{summary}")])
            return [summary_msg] + to_keep
        except Exception:
            logger.exception("summarize_all failed; truncating tail")
            return messages[-5:]

    if total_words > max_words:
        messages_to_keep, messages_to_summarize = get_last_n_messages_by_word_count(
            messages, keep_last_n=keep_last_n, max_words=max_words
        )
        if messages_to_summarize:
            try:
                excerpt = _messages_plain_excerpt(messages_to_summarize)
                summary = await _llm_summarize_excerpt(excerpt)
                summary_msg = ModelResponse(parts=[TextPart(content=f"[Earlier conversation summary]\n{summary}")])
                return [summary_msg] + messages_to_keep
            except Exception:
                logger.exception("summarize_old_messages failed; keeping recent window only")
                return messages_to_keep
        return messages_to_keep

    return messages

def _map_to_db_schema(
    msg: Dict[str, Any],
    user_id: str,
    conversation_id: str,
    new_message_id: str,  # The ID generated for the current message
    parent_message_id_override: Optional[str] = None,  # The ID of the previous message in the batch
) -> Dict[str, Any]:
    """Maps a pydantic-ai message dict to snake_case fields matching the real
    chat-history tables (game_master_chat_history / npc_chat_history /
    tutor_chat_history — see db/scripts/init_db.sql). This is an intermediate
    shape internal to save_chat_history_to_storage(); nothing else reads it."""

    # Extract core fields
    kind = msg.get("kind", "request")  # 'request' or 'response'

    # Default message fields (assume single part for content)
    # Safely extract content from 'parts' list
    part = msg.get("parts", [{}])[0]
    content = part.get("content", "")

    # Note: timestamp in the message 'part' is preferred, fallback to top-level key or now
    # Ensure timestamp is a datetime object if possible for isoformat()
    raw_timestamp = part.get("timestamp") or msg.get("timestamp")
    timestamp = datetime.now()  # Default fallback
    if isinstance(raw_timestamp, str):
        try:
            from dateutil import parser
            timestamp = parser.isoparse(raw_timestamp)
        except (ValueError, ImportError):
            # If string isn't isoformat, use current time
            timestamp = datetime.now()
    elif isinstance(raw_timestamp, datetime):
        timestamp = raw_timestamp

    # Extract LLM-specific fields for metadata
    model_name = msg.get("model_name")
    usage = msg.get("usage", {})
    instructions = msg.get("instructions")

    # Calculate token count
    token_count = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

    # Determine role ('user' or 'assistant')
    role = "assistant" if kind == "response" else "user"

    # Collect fields that don't map directly to a flat DB column
    metadata_fields = {
        "kind": kind,
        "instructions": instructions,
        "usage": usage,
        "part_kind": part.get("part_kind"),
        "uploaded_media": msg.get("uploaded_media"),
    }
    metadata_fields = {k: v for k, v in metadata_fields.items() if v is not None}

    db_row = {
        "id": new_message_id,
        "conversation_id": str(conversation_id),
        "user_id": str(user_id),
        "role": role,
        "message": content,
        "created_at": timestamp,
        "model_used": model_name,
        "token_count": token_count,
        "is_visible": True,
        "parent_message_id": parent_message_id_override or msg.get("parent_message_id"),
        "metadata": json.dumps(metadata_fields) if metadata_fields else None,
    }

    # Remove keys where the value is None to keep the insertion clean
    return {k: v for k, v in db_row.items() if v is not None}


def _handle_db_conversion(
    flat_messages: List[Any],
    user_id: str,
    conversation_id: str,
    is_old_session: bool = False,
    uploaded_media: Optional[Dict[str, Any]] = None,
) -> List[Dict]:
    """
    Handles the two-step conversion required when to_json=True, including
    managing sequential message IDs for thread chaining.
    """
    # 1. Convert to standard JSON-compatible dicts
    jsonable_messages = to_jsonable_python(flat_messages)

    if is_old_session:
        return jsonable_messages

    db_rows = []
    # Tracks the ID of the message just mapped/created (used as the parent_message_id of the *next* message)
    last_message_id: Optional[str] = None

    for i, msg in enumerate(jsonable_messages):
        msg = dict(msg) if isinstance(msg, dict) else msg
        if isinstance(msg, dict) and uploaded_media and msg.get("kind") == "response":
            msg = {**msg, "uploaded_media": uploaded_media}
        current_message_id = msg.get("chat_id") or msg.get("id") or str(uuid.uuid4())

        # Determine the parent ID (Thread Chaining Logic):
        # 1. If the input message already specifies a parent_message_id (e.g., loaded from DB or a complex reply), use it.
        # 2. Otherwise, use the ID of the message we just processed (last_message_id).
        input_parent_id = msg.get("parent_message_id")

        # The parent ID used for the DB row is the explicit input, or the ID of the immediately preceding message in this batch.
        parent_id_for_db = input_parent_id if input_parent_id is not None else last_message_id
        conversation_id = msg.get("conversation_id") or conversation_id
        # Map to DB schema using the explicit IDs
        db_row = _map_to_db_schema(
            msg,
            user_id,
            conversation_id,
            new_message_id=current_message_id,
            parent_message_id_override=parent_id_for_db
        )
        db_rows.append(db_row)
        
        # Update the tracking variable for the next iteration
        last_message_id = current_message_id

    return db_rows


def process_chat_history(
    messages: Union[
        str, 
        List[str], 
        List[Dict[str, Any]], 
        List[List[Dict[str, Any]]], 
        List[Union[ModelRequest, ModelResponse]], 
        List[List[Union[ModelRequest, ModelResponse]]]
    ],
    to_json: bool = False
):
    """
    Fast conversion between JSON-serializable (DB/Redis) and Pydantic-AI-compatible chat history formats.
    Optimized to avoid unnecessary loops and conversions.
    
    Args:
        messages: The input chat history (any supported format).
        to_json: If True, converts to DB schema dicts (for storage/Redis). 
                 If False, converts to validated Pydantic objects (for model inference).

    Returns:
        Converted chat history object or [] if empty.
    """
    if not messages:
        return []

    # 🧩 1. Handle raw string
    if isinstance(messages, str):
        result = [{
            "parts": [{"content": messages, "timestamp": datetime.now().isoformat(), "part_kind": "user-prompt"}],
            "kind": "request"
        }]
        return result if to_json else ModelMessagesTypeAdapter.validate_python(result)

    # 🧩 2. Handle list of strings
    if isinstance(messages, list) and messages and isinstance(messages[0], str):
        result = [
            {"parts": [{"content": m, "timestamp": datetime.now().isoformat(), "part_kind": "user-prompt"}], "kind": "request"}
            for m in messages
        ]
        return result if to_json else ModelMessagesTypeAdapter.validate_python(result)

    # 🧩 3. Handle Pydantic objects (ModelRequest / ModelResponse) - fastest path
    if isinstance(messages, list) and messages and isinstance(messages[0], (ModelRequest, ModelResponse)):
        return to_jsonable_python(messages) if to_json else messages
    
    # 🧩 4. Handle list of list of ModelRequest/ModelResponse
    if isinstance(messages, list) and messages and isinstance(messages[0], list) and messages[0] and isinstance(messages[0][0], (ModelRequest, ModelResponse)):
        try:
            return to_jsonable_python(messages) if to_json else ModelMessagesTypeAdapter.validate_python(messages)
        except Exception as e:
            logging.error(f"Error validating messages: {e}")
            flat = []
            for session in messages:
                flat.extend(session)
            return to_jsonable_python(flat) if to_json else ModelMessagesTypeAdapter.validate_python(flat)

    # 🧩 5. Handle list of dicts (JSON-compatible OR from DB) - most common case
    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        try:
            # Try direct validation first (fastest)
            return ModelMessagesTypeAdapter.validate_python(messages) if not to_json else messages
        except Exception as e:
            # Direct validation failed, will convert
            pass
            # Fallback: convert dicts to proper format
            result = []
            for each_msg in messages:
                # Fast path: already in correct format
                if "kind" in each_msg and "parts" in each_msg:
                    result.append(each_msg)
                    continue
                
                # Convert from DB/legacy format
                kind = each_msg.get("kind") or ("response" if each_msg.get("Role", "").lower() == "ai" or each_msg.get("role", "").lower() == "assistant" else "request")
                content = each_msg.get("content") or each_msg.get("Message") or each_msg.get("message") or (each_msg.get("parts", [{}])[0].get("content") if each_msg.get("parts") else "")
                raw_ts = each_msg.get("timestamp") or each_msg.get("created_at") or each_msg.get("CreatedOn")
                if raw_ts:
                    if isinstance(raw_ts, str):
                        try:
                            from dateutil import parser
                            timestamp = parser.isoparse(raw_ts)
                        except (ValueError, ImportError):
                            timestamp = datetime.now()
                    elif isinstance(raw_ts, datetime):
                        timestamp = raw_ts
                    else:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
                
                if kind == "request":
                    msg = {
                        "parts": [{"content": content, "timestamp": timestamp, "part_kind": "user-prompt"}],
                        "kind": "request"
                    }
                else:
                    msg = {
                        "parts": [{"content": content, "timestamp": timestamp, "part_kind": "text"}],
                        "usage": each_msg.get("usage", {}),
                        "model_name": each_msg.get("model_name") or each_msg.get("model_used"),
                        "timestamp": timestamp,
                        "kind": "response"
                    }
                result.append(msg)
            
            return result if to_json else ModelMessagesTypeAdapter.validate_python(result)

    # 🧩 6. Handle list of list of dicts (multiple sessions)
    if isinstance(messages, list) and messages and isinstance(messages[0], list) and messages[0] and isinstance(messages[0][0], dict):
        flat = []
        for session in messages:
            flat.extend(session)
        return process_chat_history(flat, to_json=to_json)

    raise ValueError(f"Unsupported chat history format: {type(messages)}")


def process_chat_history_for_model_inference(
    messages: Union[
        Dict[str, Any],
        List[Dict[str, Any]],
        List[List[Dict[str, Any]]],
        List[Union[ModelRequest, ModelResponse]],
    ]
) -> List[Union[ModelRequest, ModelResponse]]:
    """
    Preprocess chat_history retrieved from database (old chat history sessions).
    Converts DB schema format to Pydantic-AI ModelMessage format for inference.
    """
    if not messages:
        return []

    # Already in pydantic-ai message form — skip DB row conversion.
    if isinstance(messages, list) and messages and isinstance(messages[0], (ModelRequest, ModelResponse)):
        return messages

    # Handle single dict
    if isinstance(messages, dict):
        messages = [messages]
    
    # Handle list of lists (multiple sessions)
    if isinstance(messages, list) and messages and isinstance(messages[0], list):
        flat = []
        for session in messages:
            flat.extend(session)
        messages = flat
    
    # Convert DB rows to ModelMessage format
    result = []
    for row in messages:
        # Extract from DB schema (chat_history table)
        role = row.get("role", "user")
        message = row.get("message", "")
        created_at = row.get("created_at") or row.get("created_on")
        metadata = row.get("metadata") or row.get("message_metadata")
        
        # Parse metadata if it's a string, or default to empty dict if None
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        elif metadata is None:
            metadata = {}
        
        # Determine kind from role
        kind = "response" if role.lower() in ["assistant", "ai"] else "request"
        
        # Parse timestamp
        if isinstance(created_at, str):
            try:
                from dateutil import parser
                timestamp = parser.isoparse(created_at)
            except (ValueError, ImportError):
                timestamp = datetime.now()
        elif isinstance(created_at, datetime):
            timestamp = created_at
        else:
            timestamp = datetime.now()
        
        if kind == "request":
            msg = {
                "parts": [{
                    "content": message,
                    "timestamp": timestamp,
                    "part_kind": metadata.get("part_kind", "user-prompt")
                }],
                "kind": "request"
            }
            if metadata.get("instructions"):
                msg["instructions"] = metadata["instructions"]
        else:
            msg = {
                "parts": [{
                    "content": message,
                    "timestamp": timestamp,
                    "part_kind": metadata.get("part_kind", "text")
                }],
                "usage": metadata.get("usage", {}),
                "model_name": row.get("model_used") or metadata.get("model_name"),
                "timestamp": timestamp,
                "kind": "response"
            }
        
        result.append(msg)
    
    # Validate and return as Pydantic objects
    return ModelMessagesTypeAdapter.validate_python(result)


def process_chat_history_for_db_storage(
    messages: Union[
        str,
        List[str],
        List[Dict[str, Any]],
        List[List[Dict[str, Any]]],
        List[Union[ModelRequest, ModelResponse]],
    ],
    user_id: str,
    conversation_id: str,
    is_old_session: bool = False,
    uploaded_media: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Optimized conversion to DB storage format (chat_history table schema).

    Args:
        messages: The input chat history (any supported format).
        user_id: The ID of the user (required for DB schema mapping).
        conversation_id: The ID of the conversation (required for DB schema mapping).
        is_old_session: If True, skip ID generation (already has IDs from DB).
        uploaded_media: Optional dict of {ref_key: content} to add to assistant message Metadata.

    Returns:
        List of DB schema dicts ready for insertion.
    """
    if not messages:
        return []

    if isinstance(messages, list) and messages and isinstance(messages[0], (ModelRequest, ModelResponse)):
        return _handle_db_conversion(messages, user_id, conversation_id, is_old_session, uploaded_media)
    standard_format = process_chat_history(messages, to_json=True)
    return _handle_db_conversion(standard_format, user_id, conversation_id, is_old_session, uploaded_media)


async def search_internet(query: str, api_key: Optional[str] = None) -> str:
    """
    Search the internet for current information
    Uses Serper API if available, otherwise falls back to basic search
    """
    import httpx
    serper_api_key = api_key or config.SERPER_API_KEY
    
    if not serper_api_key:
        # Fallback: return empty (agent will use its knowledge)
        return ""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": serper_api_key,
                    "Content-Type": "application/json"
                },
                json={"q": query},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract relevant information
                results = []
                if "organic" in data:
                    for item in data["organic"][:5]:  # Top 5 results
                        results.append(f"{item.get('title', '')}: {item.get('snippet', '')}")
                
                return "\n".join(results)
    except Exception as e:
        logger.warning(f"Internet search error: {e}")

    return ""


# ============================================
# CHAT HISTORY STORAGE FUNCTIONS
# ============================================

async def save_chat_history_to_storage(
    chat_history: List[Union[ModelRequest, ModelResponse]],
    user_id: str,
    conversation_id: str,
    chat_type: str = "game_master",  # "game_master", "npc", "tutor"
    npc_id: Optional[str] = None,
    background: bool = True,
    tutor_document_id: Optional[str] = None,
) -> bool:
    """
    Save chat history to Redis (fast) and DB (persistent).
    Can run in background job if background=True.
    
    Args:
        chat_history: List of ModelRequest/ModelResponse objects
        user_id: User ID
        conversation_id: Session/conversation ID (game_id, document_id, etc.)
        chat_type: Type of chat ("game_master", "npc", "tutor")
        npc_id: NPC ID if chat_type is "npc"
        background: If True, schedule as background job
        
    Returns:
        True if saved successfully
    """
    try:
        from service.redis_service import get_redis_service
        from service.database import get_database_service
        
        # Convert to DB format
        db_rows = process_chat_history_for_db_storage(
            chat_history,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        if not db_rows:
            return True  # Nothing to save
        
        # Save to Redis (fast retrieval)
        redis_service = await get_redis_service()
        # Use proper Redis key format
        if npc_id:
            redis_key = f"{chat_type}_chat:{user_id}:{conversation_id}:{npc_id}"
        else:
            redis_key = f"{chat_type}_chat:{user_id}:{conversation_id}"
        
        await redis_service.set_chat_session(
            user_id=user_id,
            session_id=conversation_id if not npc_id else f"{conversation_id}:{npc_id}",
            chat_history=db_rows,
            ttl=3600  # 1 hour
        )
        
        # Save to DB (persistent storage)
        db_service = get_database_service()
        
        if chat_type == "game_master":
            for row in db_rows:
                await db_service.create_game_master_chat_message(
                    user_id=user_id,
                    game_id=conversation_id,
                    session_id=conversation_id,
                    role=row.get("role", "user"),
                    message=row.get("message", ""),
                    metadata=row.get("metadata", {})
                )
        elif chat_type == "npc":
            if not npc_id:
                raise ValueError("npc_id required for NPC chat history")
            for row in db_rows:
                await db_service.create_npc_chat_message(
                    user_id=user_id,
                    game_id=conversation_id,
                    npc_id=npc_id,
                    session_id=conversation_id,
                    role=row.get("role", "user"),
                    message=row.get("message", ""),
                    metadata=row.get("metadata", {})
                )
        elif chat_type == "tutor":
            doc_for_row = tutor_document_id or conversation_id
            for row in db_rows:
                await db_service.create_tutor_chat_message(
                    user_id=user_id,
                    document_id=doc_for_row,
                    session_id=conversation_id,
                    role=row.get("role", "user"),
                    message=row.get("message", ""),
                    sources=row.get("sources", []),
                    metadata=row.get("metadata", {})
                )
        
        return True
    except Exception as e:
        logger.error(f"Failed to save chat history: {e}")
        return False


async def get_chat_history_from_storage(
    user_id: str,
    conversation_id: str,
    chat_type: str = "game_master",
    npc_id: Optional[str] = None,
    document_id: Optional[str] = None,
    use_redis: bool = True
) -> List[Union[ModelRequest, ModelResponse]]:
    """
    Retrieve chat history from Redis (fast) or DB (cold retrieval).
    
    Args:
        user_id: User ID
        conversation_id: Session/conversation ID
        chat_type: Type of chat ("game_master", "npc", "tutor")
        npc_id: NPC ID if chat_type is "npc"
        use_redis: If True, try Redis first, then fallback to DB
        
    Returns:
        List of ModelRequest/ModelResponse objects
    """
    try:
        from service.redis_service import get_redis_service
        from service.database import get_database_service
        
        # Try Redis first (fast)
        if use_redis:
            redis_service = await get_redis_service()
            # Use proper session_id format for NPCs
            session_id_for_redis = f"{conversation_id}:{npc_id}" if npc_id else conversation_id
            redis_data = await redis_service.get_chat_session(
                user_id=user_id,
                session_id=session_id_for_redis
            )
            if redis_data:
                # Convert from DB format to ModelMessage format
                return process_chat_history_for_model_inference(redis_data)
        
        # Fallback to DB (cold retrieval)
        db_service = get_database_service()
        
        if chat_type == "game_master":
            db_rows = await db_service.get_game_master_chat_history(
                user_id=user_id,
                game_id=conversation_id,
                session_id=conversation_id
            )
        elif chat_type == "npc":
            if not npc_id:
                raise ValueError("npc_id required for NPC chat history")
            db_rows = await db_service.get_npc_chat_history(
                user_id=user_id,
                game_id=conversation_id,
                npc_id=npc_id,
                session_id=conversation_id
            )
        elif chat_type == "tutor":
            # Use document_id if provided, otherwise use conversation_id
            doc_id = document_id or conversation_id
            db_rows = await db_service.get_tutor_chat_history(
                user_id=user_id,
                document_id=doc_id,
                session_id=conversation_id
            )
        else:
            return []
        
        # Convert from DB format to ModelMessage format
        return process_chat_history_for_model_inference(db_rows)
        
    except Exception as e:
        logger.error(f"Failed to retrieve chat history: {e}")
        return []

