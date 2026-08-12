import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "alive"
    assert payload["service"] == "Code Belaraby API"

@pytest.mark.asyncio
async def test_readiness_probe(async_client: AsyncClient):
    response = await async_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "ready"


@pytest.mark.asyncio
async def test_detailed_health_exposes_only_high_level_status(async_client: AsyncClient):
    response = await async_client.get("/health/detailed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"healthy", "degraded"}
    assert "checks" in payload
    assert "password_reset_delivery" in payload["checks"]
    assert "postgresql://" not in response.text
    assert "SECRET_KEY" not in response.text
