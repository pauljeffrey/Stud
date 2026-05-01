"""
LLM-as-judge: given a transcript and expected criteria, returns pass/fail + reason.

Uses OpenAI Chat Completions when OPENAI_API_KEY (or JUDGE_API_KEY) is set.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import httpx


async def judge_transcript(
    *,
    transcript: str,
    scenario_name: str,
    expected_behavior: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Returns {"passed": bool, "reason": str, "skipped": bool}
    """
    key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("JUDGE_API_KEY")
    if not key:
        return {
            "passed": False,
            "reason": "No API key; LLM judge skipped",
            "skipped": True,
        }

    system = (
        "You are a strict test judge. Given a conversation transcript and expected behavior, "
        "decide if the system under test satisfied the expectation. "
        "Reply with JSON only: {\"passed\": true|false, \"reason\": \"...\"}"
    )
    user = (
        f"Scenario: {scenario_name}\n\n"
        f"Expected behavior:\n{expected_behavior}\n\n"
        f"Transcript:\n{transcript}\n"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0,
            },
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()
        # strip markdown fences
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text)
        return {
            "passed": bool(parsed.get("passed")),
            "reason": str(parsed.get("reason", "")),
            "skipped": False,
        }
