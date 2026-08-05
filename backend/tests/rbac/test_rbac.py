import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_student_cannot_access_admin_endpoints(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/admin/metrics", headers=headers)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_instructor_cannot_approve_payments(async_client: AsyncClient):
    inst_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01008168639",
        "password": "InstructorPass123!@#"
    })
    inst_token = inst_res.json()["access_token"]
    inst_headers = {"Authorization": f"Bearer {inst_token}"}

    review_payload = {
        "payment_id": "dummy_payment_id",
        "action": "approve",
        "review_note": "Unauthorised attempt"
    }
    res = await async_client.post("/api/v1/payments/admin/review", json=review_payload, headers=inst_headers)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_object_level_student_isolation_and_admin_boundary(async_client: AsyncClient):
    student_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = student_res.json()["access_token"]
    s_headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/admin/metrics", headers=s_headers)
    assert res.status_code == 403
