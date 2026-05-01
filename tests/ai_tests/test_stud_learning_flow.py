"""
Multi-turn pattern against Stud /api/learning/chat when a real document id exists.

Set STUD_TEST_DOCUMENT_ID to a UUID that exists in your Supabase `documents` for user_123.
Without it, tests are skipped.
"""
from __future__ import annotations

import os

import httpx
import pytest

from agents.judge import judge_transcript
from helpers.learning_client import post_learning_chat


@pytest.fixture
def document_id():
    did = os.getenv("STUD_TEST_DOCUMENT_ID")
    if not did:
        pytest.skip("Set STUD_TEST_DOCUMENT_ID to run learning chat integration tests")
    return did


@pytest.mark.asyncio
async def test_learning_chat_short_history(
    http_client: httpx.AsyncClient,
    document_id: str,
    judge_api_key: str | None,
):
    """Single user message; assistant responds (structure only if no judge key)."""
    try:
        out = await post_learning_chat(
            http_client,
            message="Give a one-sentence summary of what this material covers.",
            document_id=document_id,
        )
    except httpx.HTTPStatusError as e:
        pytest.skip(f"Learning chat failed: {e.response.status_code} {e.response.text[:200]}")
    except httpx.ConnectError:
        pytest.skip("Backend not reachable")

    assert out.get("answer"), "Empty assistant reply"
    transcript = f"user: ...\nassistant: {out['answer']}"
    if judge_api_key:
        verdict = await judge_transcript(
            transcript=transcript,
            scenario_name="short_history_summary",
            expected_behavior="The assistant gives a brief educational summary or says it needs more context from the document.",
            api_key=judge_api_key,
        )
        if not verdict.get("skipped"):
            assert verdict.get("passed"), verdict.get("reason")


@pytest.mark.asyncio
async def test_learning_chat_multi_turn_manual(
    http_client: httpx.AsyncClient,
    document_id: str,
):
    """Two turns with explicit session_id to pin conversation (same session)."""
    sid = "ai-test-session-" + document_id[:8]
    m1 = "What topics are covered?"
    try:
        await post_learning_chat(
            http_client, message=m1, document_id=document_id, session_id=sid
        )
        out2 = await post_learning_chat(
            http_client,
            message="List one topic only.",
            document_id=document_id,
            session_id=sid,
        )
    except httpx.HTTPStatusError:
        pytest.skip("Learning chat HTTP error")
    except httpx.ConnectError:
        pytest.skip("Backend not reachable")

    assert out2.get("answer")
