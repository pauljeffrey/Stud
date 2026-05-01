"""Smoke tests against deployed Stud backend (Docker: port 8000)."""
import pytest
import httpx


@pytest.mark.asyncio
async def test_root(http_client: httpx.AsyncClient):
    r = await http_client.get("/")
    assert r.status_code == 200
    assert "Stud" in r.json().get("message", "")


@pytest.mark.asyncio
async def test_health(http_client: httpx.AsyncClient):
    r = await http_client.get("/health")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data
