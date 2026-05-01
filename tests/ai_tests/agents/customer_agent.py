"""
Simulated customer: generates the next user message using an LLM (role-play).

Used to drive multi-turn tests against the deployed API when OPENAI_API_KEY is set.
"""
from __future__ import annotations

import os
from typing import List, Optional

import httpx


async def generate_customer_message(
    *,
    scenario_goal: str,
    conversation_so_far: List[dict],
    turn_index: int,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    conversation_so_far: [{"role": "user"|"assistant", "content": "..."}]
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY required for customer_agent.generate_customer_message")

    system = (
        "You are simulating a customer in a test. Output ONLY the next user message, "
        "no preamble. Stay in character. Be concise (1-3 sentences)."
    )
    hist = "\n".join(f"{m['role']}: {m['content']}" for m in conversation_so_far[-8:])
    user = (
        f"Scenario goal: {scenario_goal}\nTurn: {turn_index}\n"
        f"Conversation:\n{hist}\n\nWrite the next user message only."
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
                "temperature": 0.7,
            },
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
