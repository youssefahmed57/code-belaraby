import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token
from app.db.models import User, UserSession
from app.services.password_reset_delivery_service import (
    clear_mock_password_reset_deliveries,
    get_mock_password_reset_deliveries,
)


async def _login(async_client: AsyncClient, identifier: str = "01011111111", password: str = "StudentPass123!@#"):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert response.status_code == 200
    return response


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
async def test_registration_rejects_passwords_that_are_too_short(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "arabic_name": "طالب كلمة مرور قصيرة",
            "phone_number": f"010{uuid.uuid4().int % 100000000:08d}",
            "password": "Abc123",
            "password_confirm": "Abc123",
            "grade_level": "first_secondary",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_registration_rejects_password_without_digit(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "arabic_name": "طالب بدون رقم",
            "phone_number": f"010{uuid.uuid4().int % 100000000:08d}",
            "password": "PasswordOnly",
            "password_confirm": "PasswordOnly",
            "grade_level": "first_secondary",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_registration_rejects_password_confirmation_mismatch(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "arabic_name": "طالب تأكيد خاطئ",
            "phone_number": f"010{uuid.uuid4().int % 100000000:08d}",
            "password": "Password123",
            "password_confirm": "Password1234",
            "grade_level": "first_secondary",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_valid_session_bound_to_exact_sid(async_client: AsyncClient):
    login_response = await _login(async_client)
    token = login_response.json()["access_token"]

    me_response = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200


@pytest.mark.asyncio
async def test_missing_or_invalid_sid_is_rejected(async_client: AsyncClient, async_session):
    student = await async_session.scalar(select(User).where(User.phone_number == "01011111111"))
    assert student is not None

    missing_sid_token = create_access_token(subject=student.id, role="student")
    missing_sid_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {missing_sid_token}"},
    )
    assert missing_sid_response.status_code == 401

    invalid_sid_token = create_access_token(subject=student.id, role="student", sid="missing-session-id")
    invalid_sid_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {invalid_sid_token}"},
    )
    assert invalid_sid_response.status_code == 401


@pytest.mark.asyncio
async def test_revoked_session_is_rejected_even_if_another_session_exists(async_client: AsyncClient, async_session):
    first_login = await _login(async_client)
    second_login = await _login(async_client)

    first_token = first_login.json()["access_token"]
    second_token = second_login.json()["access_token"]
    first_sid = decode_access_token(first_token)["sid"]

    first_session = await async_session.scalar(select(UserSession).where(UserSession.id == first_sid))
    assert first_session is not None
    first_session.is_active = False
    await async_session.commit()

    revoked_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    assert revoked_response.status_code == 401

    active_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {second_token}"},
    )
    assert active_response.status_code == 200


@pytest.mark.asyncio
async def test_expired_session_is_rejected(async_client: AsyncClient, async_session):
    login_response = await _login(async_client)
    token = login_response.json()["access_token"]
    sid = decode_access_token(token)["sid"]

    session = await async_session.scalar(select(UserSession).where(UserSession.id == sid))
    assert session is not None
    session.expires_at = datetime.utcnow() - timedelta(minutes=5)
    await async_session.commit()

    me_response = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_logout_current_device_only_revokes_current_sid(async_client: AsyncClient):
    first_login = await _login(async_client)
    second_login = await _login(async_client)

    first_token = first_login.json()["access_token"]
    second_token = second_login.json()["access_token"]
    first_session_token = first_login.cookies.get("session_token")
    second_session_token = second_login.cookies.get("session_token")
    async_client.cookies.set("session_token", first_session_token or "")

    logout_response = await async_client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {first_token}",
            "X-Session-Token": first_session_token or "",
        },
    )
    assert logout_response.status_code == 200

    first_me = await async_client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {first_token}",
            "X-Session-Token": first_session_token or "",
        },
    )
    assert first_me.status_code == 401

    async_client.cookies.set("session_token", second_session_token or "")
    second_me = await async_client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {second_token}",
            "X-Session-Token": second_session_token or "",
        },
    )
    assert second_me.status_code == 200


@pytest.mark.asyncio
async def test_session_revocation_and_logout_all(async_client: AsyncClient):
    login_response = await _login(async_client)
    token = login_response.json()["access_token"]

    logout_response = await async_client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_response.status_code == 200

    me_response = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_disabled_user_authentication_fails(async_client: AsyncClient, async_session):
    login_response = await _login(async_client)
    token = login_response.json()["access_token"]

    student = await async_session.scalar(select(User).where(User.phone_number == "01011111111"))
    assert student is not None
    previous_status = student.status
    student.status = "disabled"
    await async_session.commit()

    try:
        me_response = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 401
    finally:
        student.status = previous_status
        await async_session.commit()


@pytest.mark.asyncio
async def test_password_reset_uses_mock_delivery_and_revokes_sessions(async_client: AsyncClient):
    clear_mock_password_reset_deliveries()
    login_response = await _login(async_client)
    old_token = login_response.json()["access_token"]

    forgot_response = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"identifier": "student1@codejourney.eg"},
    )
    assert forgot_response.status_code == 200
    assert "reset_token" not in forgot_response.json()

    deliveries = get_mock_password_reset_deliveries()
    assert len(deliveries) == 1
    raw_token = deliveries[-1]["token"]

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

    old_token_response = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert old_token_response.status_code == 401

    clear_mock_password_reset_deliveries()
    restore_request = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"identifier": "student1@codejourney.eg"},
    )
    assert restore_request.status_code == 200
    restore_token = get_mock_password_reset_deliveries()[-1]["token"]
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


@pytest.mark.asyncio
async def test_password_reset_rejects_invalid_password_policy_and_mismatch(async_client: AsyncClient):
    forgot_response = await async_client.post(
        "/api/v1/auth/forgot-password",
        json={"identifier": "student1@codejourney.eg"},
    )
    assert forgot_response.status_code == 200
    raw_token = get_mock_password_reset_deliveries()[-1]["token"]

    short_password = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "Abc123", "password_confirm": "Abc123"},
    )
    assert short_password.status_code == 400

    no_digit = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "PasswordOnly", "password_confirm": "PasswordOnly"},
    )
    assert no_digit.status_code == 400

    mismatch = await async_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "Password123", "password_confirm": "Password124"},
    )
    assert mismatch.status_code == 400


@pytest.mark.asyncio
async def test_failed_login_backoff_is_temporary_and_resets_after_success(async_client: AsyncClient):
    for _ in range(4):
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"identifier": "01011111111", "password": "WrongPassword123!"},
        )
        assert response.status_code == 401

    success_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    assert success_response.status_code == 200

    for _ in range(4):
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"identifier": "01011111111", "password": "WrongPassword123!"},
        )
        assert response.status_code == 401

    throttled_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "WrongPassword123!"},
    )
    assert throttled_response.status_code == 429


@pytest.mark.asyncio
async def test_forgot_password_fails_safely_without_provider_in_production(async_client: AsyncClient):
    original_environment = settings.ENVIRONMENT
    original_provider = settings.PASSWORD_RESET_DELIVERY_PROVIDER
    try:
        settings.ENVIRONMENT = "production"
        settings.PASSWORD_RESET_DELIVERY_PROVIDER = "disabled"
        response = await async_client.post(
            "/api/v1/auth/forgot-password",
            json={"identifier": "student1@codejourney.eg"},
        )
        assert response.status_code == 503
        assert "reset_token" not in response.text
    finally:
        settings.ENVIRONMENT = original_environment
        settings.PASSWORD_RESET_DELIVERY_PROVIDER = original_provider


@pytest.mark.asyncio
async def test_csrf_invalid_origin_is_rejected_for_cookie_session(async_client: AsyncClient):
    original_trusted = list(settings.CSRF_TRUSTED_ORIGINS)
    try:
        settings.CSRF_TRUSTED_ORIGINS = ["https://app.codebelaraby.example"]
        login_response = await _login(async_client)
        csrf_token = login_response.cookies.get("csrf_token")
        assert csrf_token

        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            headers={
                "Origin": "https://evilcodebelaraby.example",
                "X-CSRF-Token": csrf_token,
            },
        )
        assert logout_response.status_code == 403
    finally:
        settings.CSRF_TRUSTED_ORIGINS = original_trusted


def test_csrf_origin_boundary_rules():
    original_trusted = list(settings.CSRF_TRUSTED_ORIGINS)
    try:
        settings.CSRF_TRUSTED_ORIGINS = [
            "https://app.codebelaraby.example",
            "https://.trusted.codebelaraby.example",
        ]
        assert settings.is_csrf_origin_trusted("https://app.codebelaraby.example") is True
        assert settings.is_csrf_origin_trusted("https://video.trusted.codebelaraby.example") is True
        assert settings.is_csrf_origin_trusted("https://trusted.codebelaraby.example") is True
        assert settings.is_csrf_origin_trusted("https://eviltrusted.codebelaraby.example") is False
        assert settings.is_csrf_origin_trusted("http://app.codebelaraby.example") is False
        assert settings.is_csrf_origin_trusted("https://app.codebelaraby.example:444") is False
    finally:
        settings.CSRF_TRUSTED_ORIGINS = original_trusted
