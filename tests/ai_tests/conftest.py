"""
Pytest fixtures for deployed-backend AI tests.

Usage:
  BASE_URL=http://localhost:8000 pytest tests/ai_tests -v
  BASE_URL=https://your-deployed-host pytest tests/ai_tests -v
"""
import os

import httpx
import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture
async def http_client(base_url: str):
    async with httpx.AsyncClient(base_url=base_url, timeout=httpx.Timeout(120.0)) as client:
        yield client


@pytest.fixture
def judge_api_key() -> str | None:
    """OpenAI key for judge LLM; tests skip deep assertions if unset."""
    return os.getenv("OPENAI_API_KEY") or os.getenv("JUDGE_API_KEY")


@pytest.fixture
def customer_api_key() -> str | None:
    """Optional: separate key for customer simulator."""
    return os.getenv("OPENAI_API_KEY") or os.getenv("CUSTOMER_SIM_API_KEY")
