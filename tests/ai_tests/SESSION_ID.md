# How `session_id` is determined in Stud

`session_id` is not a single global concept; it is **per feature** and usually doubles as the **conversation id** used for Redis/DB chat storage.

## Learning / tutor chat (`/api/learning/chat`)

Resolved in `python_backend/api/learning.py` inside the streaming handler:

1. **`request.session_id`** — if the client sends an explicit session id, it wins.
2. Else **`request.enrollment_id`** — when resuming a learning journey (enrollment-scoped chat).
3. Else **`document_id`** — after resolving from enrollment when only `enrollmentId` is sent.
4. The tutor agent (`tutor_agent.py`) uses the same idea for **`conversation_id`**:
   - `conversation_id = session_id or enrollment_id or document_id or f"tutor-{user_id}"`

That `conversation_id` is what **`get_chat_history_from_storage`** and **`save_chat_history_to_storage`** use (together with `document_id` for tutor rows). The DB column `tutor_chat_history.session_id` stores this value.

## Game / Mediquest (`game_v2`)

- **`InitializeGameRequest.session_id`**: for **demo** flows, a `demo_session_id` may be generated or passed; it ties demo users to Redis keys like `demo_game:{demo_session_id}`.
- **NPC / game master chat**: `session_id` defaults to **`game_state.game_id`** when not provided (`api/game_v2.py`).

## Redis keys (`redis_service.py`)

Chat sessions use keys like `chat_session:{user_id}:{session_id}` (and variants for NPCs).

## Summary

| Flow | Typical `session_id` / conversation id |
|------|----------------------------------------|
| Tutor, document-only | `document_id` or client `session_id` |
| Tutor, enrollment | `enrollment_id` (or explicit `session_id`) |
| Game | `game_id` from `game_state` |

Clients should send a **stable** id per conversation (document, enrollment, or game) so history loads correctly.
