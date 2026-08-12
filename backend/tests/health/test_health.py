import pytest
from httpx import AsyncClient

from app.core.config import settings

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


@pytest.mark.asyncio
async def test_detailed_health_requires_token_in_production(async_client: AsyncClient):
    original_environment = settings.ENVIRONMENT
    original_token = settings.HEALTH_MONITOR_TOKEN
    try:
        settings.ENVIRONMENT = "production"
        settings.HEALTH_MONITOR_TOKEN = "monitor-token"

        missing_token = await async_client.get("/health/detailed")
        assert missing_token.status_code == 401

        invalid_token = await async_client.get(
            "/health/detailed",
            headers={"X-Health-Monitor-Token": "wrong-token"},
        )
        assert invalid_token.status_code == 401

        valid_token = await async_client.get(
            "/health/detailed",
            headers={"X-Health-Monitor-Token": "monitor-token"},
        )
        assert valid_token.status_code == 200
    finally:
        settings.ENVIRONMENT = original_environment
        settings.HEALTH_MONITOR_TOKEN = original_token


@pytest.mark.asyncio
async def test_detailed_health_fails_closed_when_token_missing_in_staging(async_client: AsyncClient):
    original_environment = settings.ENVIRONMENT
    original_token = settings.HEALTH_MONITOR_TOKEN
    try:
        settings.ENVIRONMENT = "staging"
        settings.HEALTH_MONITOR_TOKEN = None
        response = await async_client.get("/health/detailed")
        assert response.status_code == 503
    finally:
        settings.ENVIRONMENT = original_environment
        settings.HEALTH_MONITOR_TOKEN = original_token
