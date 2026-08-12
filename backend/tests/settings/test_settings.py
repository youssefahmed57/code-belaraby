import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.db.models import PlatformSettings


@pytest.mark.asyncio
async def test_public_settings_expose_payment_numbers_without_leaking_private_keys(
    async_client: AsyncClient,
    async_session,
):
    instapay_legacy = await async_session.scalar(
        select(PlatformSettings).where(PlatformSettings.key == "instapay_account")
    )
    assert instapay_legacy is not None

    await async_session.execute(delete(PlatformSettings).where(PlatformSettings.key == "instapay_number"))
    async_session.add(PlatformSettings(key="smtp_password", value="super-secret-should-not-leak"))
    await async_session.commit()

    response = await async_client.get("/api/v1/settings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["instapay_number"] == instapay_legacy.value
    assert payload["vodafone_cash_number"] == "01001340533"
    assert "instapay_account" not in payload
    assert "smtp_password" not in payload
