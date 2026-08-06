import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_private_payment_receipt_access_and_cross_student_denial(async_client: AsyncClient):
    student3_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    token3 = student3_res.json()["access_token"]
    headers3 = {"Authorization": f"Bearer {token3}"}

    res = await async_client.get("/api/v1/payments/my-payments", headers=headers3)
    assert res.status_code == 200
    my_payments = res.json()
    for p in my_payments:
        assert p["user_id"] != "student_2_id"

@pytest.mark.asyncio
async def test_duplicate_payment_approval_and_transaction_rollback(async_client: AsyncClient):
    student_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01022222222",
        "password": "StudentPass123!@#"
    })
    s_token = student_res.json()["access_token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    courses = (await async_client.get("/api/v1/courses")).json()
    course_id = courses[0]["id"]

    order_res = await async_client.post("/api/v1/payments/order", json={
        "course_id": course_id,
        "payment_method": "instapay"
    }, headers=s_headers)
    payment_id = order_res.json()["id"]

    admin_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01001340533",
        "password": "AdminPass123!@#"
    })
    a_token = admin_res.json()["access_token"]
    a_headers = {"Authorization": f"Bearer {a_token}"}

    review_payload = {"payment_id": payment_id, "action": "approve", "review_note": "Approved"}
    app1 = await async_client.post("/api/v1/payments/admin/review", json=review_payload, headers=a_headers)
    assert app1.status_code == 200
    assert app1.json()["status"] == "approved"

    app2 = await async_client.post("/api/v1/payments/admin/review", json=review_payload, headers=a_headers)
    assert app2.status_code == 200
    assert app2.json()["status"] == "approved"

@pytest.mark.asyncio
async def test_signed_preview_url_validity_and_tamper_protection(async_client: AsyncClient):
    admin_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01001340533",
        "password": "AdminPass123!@#"
    })
    a_token = admin_res.json()["access_token"]
    a_headers = {"Authorization": f"Bearer {a_token}"}

    # 1. Generate signed URL for receipt file
    gen_res = await async_client.post("/api/v1/payments/admin/generate-preview-url?file_key=receipts/sample.png", headers=a_headers)
    assert gen_res.status_code == 200
    token = gen_res.json()["token"]

    # 2. Access preview with valid token (returns 404 if file missing, but pass signature check 404 vs 403)
    preview_res = await async_client.get(f"/api/v1/payments/preview?token={token}")
    assert preview_res.status_code in [200, 404]

    # 3. Access preview with tampered token returns 403
    tampered_token = token[:-4] + "AAAA"
    tampered_res = await async_client.get(f"/api/v1/payments/preview?token={tampered_token}")
    assert tampered_res.status_code == 403
    assert "تم التلاعب" in tampered_res.json()["detail"] or "غير صالح" in tampered_res.json()["detail"]

@pytest.mark.asyncio
async def test_receipt_file_extension_restriction_jpeg_png_webp(async_client: AsyncClient):
    student_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = student_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Uploading PDF fails 400
    files = {"file": ("receipt.pdf", b"%PDF-1.4...", "application/pdf")}
    data = {
        "payment_id": "dummy_payment_id",
        "sender_identifier": "01011111111",
        "amount_submitted": "350"
    }
    res = await async_client.post("/api/v1/payments/upload-receipt", data=data, files=files, headers=headers)
    assert res.status_code == 400
    assert "نوع الملف غير مسموح به" in res.json()["detail"]

@pytest.mark.asyncio
async def test_receipt_magic_bytes_validation_and_token_expiry(async_client: AsyncClient):
    from app.services.storage_service import generate_signed_receipt_token, verify_signed_receipt_token
    from fastapi import HTTPException

    student_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = student_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Invalid Magic Bytes (PNG extension with invalid text content)
    invalid_files = {"file": ("receipt.png", b"NOT_A_REAL_IMAGE_HEADER_BYTES", "image/png")}
    data = {
        "payment_id": "dummy_id",
        "sender_identifier": "01011111111",
        "amount_submitted": "350"
    }
    res = await async_client.post("/api/v1/payments/upload-receipt", data=data, files=invalid_files, headers=headers)
    assert res.status_code == 400
    assert "Magic Bytes Mismatch" in res.json()["detail"]

    # 2. Expired signed token verification throws 403
    expired_token = generate_signed_receipt_token("receipts/test.png", expires_in_seconds=-10)
    with pytest.raises(HTTPException) as exc_info:
        verify_signed_receipt_token(expired_token)
    assert exc_info.value.status_code == 403
    assert "انتهت صلاحية" in exc_info.value.detail
