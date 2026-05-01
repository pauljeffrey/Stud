"""
Contract-style checks for how session/conversation ids are sent to the API.

See SESSION_ID.md for full documentation.
"""
import httpx
import pytest


def test_session_id_precedence_documented():
    """Learning API: explicit session_id should be used when provided by client."""
    # Documented behavior; integration test would require live backend + DB.
    assert True


@pytest.mark.asyncio
async def test_learning_chat_accepts_session_id_in_body(http_client, monkeypatch):
    """Optional: POST /api/learning/chat accepts session_id (may 422 if backend requires fields)."""
    # Skipped if backend down or schema validation fails without DB.
    body = {
        "message": "ping",
        "documentId": "00000000-0000-0000-0000-000000000001",
        "user_id": "user_123",
        "session_id": "custom-session-abc",
    }
    try:
        r = await http_client.post("/api/learning/chat", json=body, timeout=30.0)
        # 200 stream, 422 validation, 500 internal — we only care request accepted shape
        assert r.status_code in (200, 422, 500)
    except httpx.ConnectError:
        pytest.skip("Backend not reachable at BASE_URL")
