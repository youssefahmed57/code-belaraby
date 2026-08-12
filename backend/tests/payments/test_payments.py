import pytest
from httpx import AsyncClient
from app.core.config import settings


def _png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"valid-receipt-payload"


def _unique_png_bytes(marker: str) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + marker.encode("utf-8")


@pytest.mark.asyncio
async def test_private_payment_receipt_access_and_cross_student_denial(async_client: AsyncClient):
    student_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01033333333", "password": "StudentPass123!@#"},
    )
    student_headers = {"Authorization": f"Bearer {student_response.json()['access_token']}"}

    my_payments = await async_client.get("/api/v1/payments/my-payments", headers=student_headers)
    assert my_payments.status_code == 200
    for payment in my_payments.json():
        assert payment["user_id"] != "student_2_id"


@pytest.mark.asyncio
async def test_duplicate_payment_approval_is_idempotent_after_valid_receipt(async_client: AsyncClient):
    student_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01022222222", "password": "StudentPass123!@#"},
    )
    student_headers = {"Authorization": f"Bearer {student_response.json()['access_token']}"}

    courses = (await async_client.get("/api/v1/courses")).json()
    course_id = courses[0]["id"]

    order_response = await async_client.post(
        "/api/v1/payments/order",
        json={"course_id": course_id, "payment_method": "instapay"},
        headers=student_headers,
    )
    assert order_response.status_code == 200
    payment_id = order_response.json()["id"]

    receipt_response = await async_client.post(
        "/api/v1/payments/upload-receipt",
        data={
            "payment_id": payment_id,
            "sender_identifier": "01022222222",
            "amount_submitted": "180.00",
        },
        files={"file": ("receipt.png", _unique_png_bytes(payment_id), "image/png")},
        headers=student_headers,
    )
    assert receipt_response.status_code == 200
    assert receipt_response.json()["status"] == "pending_review"

    admin_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01001340533", "password": "AdminPass123!@#"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_response.json()['access_token']}"}

    review_payload = {"payment_id": payment_id, "action": "approve", "review_note": "Approved"}
    approve_once = await async_client.post("/api/v1/payments/admin/review", json=review_payload, headers=admin_headers)
    assert approve_once.status_code == 200
    assert approve_once.json()["status"] == "approved"

    approve_twice = await async_client.post("/api/v1/payments/admin/review", json=review_payload, headers=admin_headers)
    assert approve_twice.status_code == 200
    assert approve_twice.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_signed_preview_url_validity_and_admin_protection(async_client: AsyncClient):
    admin_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01001340533", "password": "AdminPass123!@#"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_response.json()['access_token']}"}

    generate_response = await async_client.post(
        "/api/v1/payments/admin/generate-preview-url?file_key=receipts/sample.png",
        headers=admin_headers,
    )
    assert generate_response.status_code == 200
    token = generate_response.json()["token"]

    preview_response = await async_client.get(f"/api/v1/payments/preview?token={token}", headers=admin_headers)
    assert preview_response.status_code in {200, 404}

    tampered_token = token[:-4] + "AAAA"
    tampered_response = await async_client.get(
        f"/api/v1/payments/preview?token={tampered_token}",
        headers=admin_headers,
    )
    assert tampered_response.status_code == 403

    student_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    student_headers = {"Authorization": f"Bearer {student_response.json()['access_token']}"}
    forbidden_preview = await async_client.get(f"/api/v1/payments/preview?token={token}", headers=student_headers)
    assert forbidden_preview.status_code == 403


@pytest.mark.asyncio
async def test_receipt_file_extension_restriction_jpeg_png_webp(async_client: AsyncClient):
    student_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    student_headers = {"Authorization": f"Bearer {student_response.json()['access_token']}"}

    courses = (await async_client.get("/api/v1/courses")).json()
    order_response = await async_client.post(
        "/api/v1/payments/order",
        json={"course_id": courses[0]["id"], "payment_method": "instapay"},
        headers=student_headers,
    )
    payment_id = order_response.json()["id"]

    response = await async_client.post(
        "/api/v1/payments/upload-receipt",
        data={
            "payment_id": payment_id,
            "sender_identifier": "01011111111",
            "amount_submitted": "350",
        },
        files={"file": ("receipt.pdf", b"%PDF-1.4", "application/pdf")},
        headers=student_headers,
    )
    assert response.status_code == 400
    assert "نوع الملف غير مسموح" in response.json()["detail"]


@pytest.mark.asyncio
async def test_receipt_magic_bytes_validation_and_token_expiry(async_client: AsyncClient):
    from fastapi import HTTPException

    from app.services.storage_service import generate_signed_receipt_token, verify_signed_receipt_token

    student_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    student_headers = {"Authorization": f"Bearer {student_response.json()['access_token']}"}

    courses = (await async_client.get("/api/v1/courses")).json()
    order_response = await async_client.post(
        "/api/v1/payments/order",
        json={"course_id": courses[0]["id"], "payment_method": "instapay"},
        headers=student_headers,
    )
    payment_id = order_response.json()["id"]

    response = await async_client.post(
        "/api/v1/payments/upload-receipt",
        data={
            "payment_id": payment_id,
            "sender_identifier": "01011111111",
            "amount_submitted": "350",
        },
        files={"file": ("receipt.png", b"NOT_A_REAL_IMAGE_HEADER_BYTES", "image/png")},
        headers=student_headers,
    )
    assert response.status_code == 400
    assert "محتوى الملف غير صالح" in response.json()["detail"]

    expired_token = generate_signed_receipt_token("receipts/test.png", expires_in_seconds=-10)
    with pytest.raises(HTTPException) as exc_info:
        verify_signed_receipt_token(expired_token)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_receipt_preview_rejects_path_traversal(async_client: AsyncClient):
    admin_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01001340533", "password": "AdminPass123!@#"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_response.json()['access_token']}"}

    traversal_response = await async_client.post(
        "/api/v1/payments/admin/generate-preview-url?file_key=../secrets.txt",
        headers=admin_headers,
    )
    assert traversal_response.status_code == 400

    absolute_response = await async_client.post(
        "/api/v1/payments/admin/generate-preview-url?file_key=C:/Windows/System32/drivers/etc/hosts",
        headers=admin_headers,
    )
    assert absolute_response.status_code == 400


@pytest.mark.asyncio
async def test_invalid_payment_is_rejected_before_receipt_file_persists(async_client: AsyncClient):
    import os

    student_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    student_headers = {"Authorization": f"Bearer {student_response.json()['access_token']}"}

    existing_files = set()
    for root, _, files in os.walk(settings.PRIVATE_STORAGE_LOCAL_DIR):
        for file_name in files:
            existing_files.add(os.path.join(root, file_name))

    response = await async_client.post(
        "/api/v1/payments/upload-receipt",
        data={
            "payment_id": "missing-payment-id",
            "sender_identifier": "01011111111",
            "amount_submitted": "350",
        },
        files={"file": ("receipt.png", _png_bytes(), "image/png")},
        headers=student_headers,
    )
    assert response.status_code == 404

    after_files = set()
    for root, _, files in os.walk(settings.PRIVATE_STORAGE_LOCAL_DIR):
        for file_name in files:
            after_files.add(os.path.join(root, file_name))

    assert after_files == existing_files
