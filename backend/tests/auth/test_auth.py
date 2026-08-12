import uuid

import pytest
from httpx import AsyncClient

from app.services.auth_service import request_password_reset


@pytest.mark.asyncio
async def test_student_registration_and_login(async_client: AsyncClient):
    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    reg_payload = {
        "arabic_name": "طالب جديد اختبار سيكيورتي",
        "phone_number": rand_phone,
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary",
    }
    response = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_invalid_login_credentials(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01099990001", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_egyptian_phone(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "arabic_name": "طالب هاتف خطأ",
            "phone_number": "123456",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "grade_level": "first_secondary",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_session_revocation_and_logout_all(async_client: AsyncClient):
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    session_cookie = login_response.cookies.get("session_token")
    headers = {"Authorization": f"Bearer {token}"}
    if session_cookie:
        headers["X-Session-Token"] = session_cookie

    logout_response = await async_client.post("/api/v1/auth/logout-all", headers=headers)
    assert logout_response.status_code == 200

    me_response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_password_reset_and_token_protection(async_client: AsyncClient, async_session):
    forgot_response = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"identifier": "student1@codejourney.eg"},
    )
    assert forgot_response.status_code == 200
    assert "reset_token" not in forgot_response.json()

    raw_token = await request_password_reset(async_session, "student1@codejourney.eg")
    assert raw_token

    invalid_response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid_tampered_token", "new_password": "NewStudentPass123!@#"},
    )
    assert invalid_response.status_code == 400

    reset_response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewStudentPass123!@#"},
    )
    assert reset_response.status_code == 200

    restore_token = await request_password_reset(async_session, "student1@codejourney.eg")
    assert restore_token
    restore_response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": restore_token, "new_password": "StudentPass123!@#"},
    )
    assert restore_response.status_code == 200

    reuse_response = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewStudentPass123!@#"},
    )
    assert reuse_response.status_code == 400
