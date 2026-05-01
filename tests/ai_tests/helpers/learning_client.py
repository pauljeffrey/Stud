"""Call Stud learning chat SSE endpoint and collect assistant text."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx


async def post_learning_chat(
    client: httpx.AsyncClient,
    *,
    message: str,
    document_id: str,
    user_id: str = "user_123",
    enrollment_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "message": message,
        "documentId": document_id,
        "user_id": user_id,
    }
    if enrollment_id:
        body["enrollmentId"] = enrollment_id
    if session_id:
        body["session_id"] = session_id

    chunks: List[str] = []
    meta: Dict[str, Any] = {}

    async with client.stream(
        "POST",
        "/api/learning/chat",
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=120.0,
    ) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            try:
                data = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            if data.get("content"):
                chunks.append(data["content"])
            if data.get("complete"):
                meta.update(
                    {
                        "generate_quiz": data.get("generate_quiz"),
                        "play_quest": data.get("play_quest"),
                        "document_id": data.get("document_id"),
                        "enrollment_id": data.get("enrollment_id"),
                    }
                )
    return {"answer": "".join(chunks), **{k: v for k, v in meta.items() if v is not None}}
