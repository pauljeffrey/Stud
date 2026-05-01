"""Non-LLM relevance and dedup helpers for document RAG and worker pipelines."""
from __future__ import annotations

from typing import Any, Dict, List


def filter_by_relevance(
    results: List[Dict[str, Any]],
    threshold: float,
    score_key: str = "score",
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    t = float(threshold)
    for r in results:
        s = r.get(score_key)
        if s is None:
            s = r.get("relevance_score")
        if s is None:
            out.append(r)
        elif float(s) >= t:
            out.append(r)
    return out


def dedup_text_snippets(
    items: List[Dict[str, Any]],
    text_key: str = "content",
    prefix_len: int = 2000,
) -> List[Dict[str, Any]]:
    seen: set[int] = set()
    out: List[Dict[str, Any]] = []
    for it in items:
        sample = (it.get(text_key) or "")[:prefix_len]
        h = hash(sample)
        if h in seen:
            continue
        seen.add(h)
        out.append(it)
    return out
