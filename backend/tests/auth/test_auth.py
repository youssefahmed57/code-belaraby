import uuid
import pytest
from httpx import AsyncClient
from app.db.models import UserSession

@pytest.mark.asyncio
async def test_student_registration_and_login(async_client: AsyncClient):
    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    reg_payload = {
        "arabic_name": "طالب جديد اختبار سكيورتي",
        "phone_number": rand_phone,
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary"
    }
    res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_invalid_login_credentials(async_client: AsyncClient):
    res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01099990001",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_invalid_egyptian_phone(async_client: AsyncClient):
    reg_payload = {
        "arabic_name": "طالب هاتف خطأ",
        "phone_number": "123456",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary"
    }
    res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_session_revocation_and_logout_all(async_client: AsyncClient):
    # 1. Login user
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    assert login_res.status_code == 200
    res_data = login_res.json()
    token = res_data["access_token"]
    
    # Get session token from cookie
    session_cookie = login_res.cookies.get("session_token")
    headers = {"Authorization": f"Bearer {token}"}
    if session_cookie:
        headers["X-Session-Token"] = session_cookie

    # 2. Perform logout-all
    logout_res = await async_client.post("/api/v1/auth/logout-all", headers=headers)
    assert logout_res.status_code == 200

    # 3. Subsequent request with old session token should fail 401
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 401
    assert "تم إلغاء هذه الجلسة" in me_res.json()["detail"] or "غير مصرح" in me_res.json()["detail"]

@pytest.mark.asyncio
async def test_password_reset_and_token_protection(async_client: AsyncClient):
    # 1. Request forgot password
    req_res = await async_client.post("/api/v1/auth/forgot-password", json={
        "identifier": "student1@codejourney.eg"
    })
    assert req_res.status_code == 200
    res_data = req_res.json()
    assert "reset_token" in res_data
    raw_token = res_data["reset_token"]

    # 2. Reset password using invalid/tampered token fails 400
    invalid_res = await async_client.post("/api/v1/auth/reset-password", json={
        "token": "invalid_tampered_token",
        "new_password": "NewStudentPass123!@#"
    })
    assert invalid_res.status_code == 400

    # 3. Reset password with valid token
    reset_res = await async_client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewStudentPass123!@#"
    })
    assert reset_res.status_code == 200

    # 4. Restore original password so other tests using student1 pass cleanly
    req_res2 = await async_client.post("/api/v1/auth/forgot-password", json={
        "identifier": "student1@codejourney.eg"
    })
    raw_token2 = req_res2.json()["reset_token"]
    await async_client.post("/api/v1/auth/reset-password", json={
        "token": raw_token2,
        "new_password": "StudentPass123!@#"
    })

    # 4. Attempting to use raw_token second time fails
    reuse_res = await async_client.post("/api/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewStudentPass123!@#"
    })
    assert reuse_res.status_code == 400
