import uuid
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_locked_lesson_direct_url_access(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/lessons/if-statements-and-decisions", headers=headers)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_unauthorised_video_token_request(async_client: AsyncClient):
    res = await async_client.get("/api/v1/videos/token/demo_video_lesson_1")
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_dashboard_summary_enrolment_filters_and_progress_isolation(async_client: AsyncClient):
    # 1. Register a fresh student (0 enrolments initially)
    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    reg_payload = {
        "arabic_name": "طالب لاختبار اللوحة",
        "phone_number": rand_phone,
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary"
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fresh student should have 0 active enrolments
    dash0 = await async_client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash0.status_code == 200
    data0 = dash0.json()
    assert data0["active_enrolment_count"] == 0
    assert len(data0["courses"]) == 0
    assert len(data0["suggested_courses"]) >= 1

    # 2. Student 3 (01033333333) should also have active_enrolment_count == len(courses)
    s3_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    token3 = s3_res.json()["access_token"]
    h3 = {"Authorization": f"Bearer {token3}"}

    dash3 = await async_client.get("/api/v1/dashboard/summary", headers=h3)
    assert dash3.status_code == 200
    data3 = dash3.json()
    assert data3["active_enrolment_count"] == len(data3["courses"])
