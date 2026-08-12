import base64
import hashlib
import hmac
import mimetypes
import os
import posixpath
import time
from typing import Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


RECEIPT_TOKEN_NAMESPACE = "receipt_preview"


def _receipt_signing_key() -> str:
    return settings.RECEIPT_SIGNING_SECRET


def _validate_private_file_key(file_key: str, namespace_prefix: str = "receipts/") -> str:
    if not file_key or "\x00" in file_key:
        raise HTTPException(status_code=400, detail="مفتاح الملف غير صالح.")

    normalized = posixpath.normpath(file_key.replace("\\", "/")).lstrip("/")
    if normalized.startswith("../") or normalized == "..":
        raise HTTPException(status_code=400, detail="مسار الملف غير صالح.")
    if os.path.isabs(file_key) or ":" in file_key.split("/")[0]:
        raise HTTPException(status_code=400, detail="المسار المطلق غير مسموح.")
    if not normalized.startswith(namespace_prefix):
        raise HTTPException(status_code=400, detail="الملف المطلوب خارج نطاق الإيصالات الخاصة.")
    return normalized


def generate_signed_receipt_token(file_key: str, expires_in_seconds: int = 300) -> str:
    normalized = _validate_private_file_key(file_key)
    exp = int(time.time()) + expires_in_seconds
    payload = f"{RECEIPT_TOKEN_NAMESPACE}:{normalized}:{exp}"
    signature = hmac.new(
        _receipt_signing_key().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    encoded = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(encoded.encode("utf-8")).decode("utf-8")


def verify_signed_receipt_token(token: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        namespace, file_key, exp_text, signature = raw.split(":", 3)
        if namespace != RECEIPT_TOKEN_NAMESPACE:
            raise HTTPException(status_code=403, detail="رمز المعاينة غير صالح لهذا المورد.")

        normalized = _validate_private_file_key(file_key)
        expires_at = int(exp_text)
        if time.time() > expires_at:
            raise HTTPException(status_code=403, detail="انتهت صلاحية رابط المعاينة المؤقت.")

        payload = f"{namespace}:{normalized}:{expires_at}"
        expected = hmac.new(
            _receipt_signing_key().encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="تم التلاعب برابط المعاينة المؤقت.")
        return normalized
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="رمز التوقيع غير صالح.")


class StorageService:
    @staticmethod
    def _private_storage_root() -> str:
        root = os.path.realpath(settings.PRIVATE_STORAGE_LOCAL_DIR)
        os.makedirs(root, exist_ok=True)
        return root

    @staticmethod
    def _resolve_private_storage_path(file_key: str) -> str:
        normalized = _validate_private_file_key(file_key)
        root = StorageService._private_storage_root()
        full_path = os.path.realpath(os.path.join(root, normalized.replace("/", os.sep)))
        if not full_path.startswith(root):
            raise HTTPException(status_code=400, detail="مسار الملف غير صالح.")
        return full_path

    @staticmethod
    async def upload_file(file_bytes: bytes, file_key: str, content_type: str = "image/png") -> str:
        normalized = _validate_private_file_key(file_key)
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            clean_base_url = settings.SUPABASE_URL.rstrip("/")
            url = f"{clean_base_url}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{normalized}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": content_type,
                "x-upsert": "true",
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, content=file_bytes, headers=headers)
                if response.status_code not in (200, 201):
                    response = await client.put(url, content=file_bytes, headers=headers)
                if response.status_code not in (200, 201):
                    raise HTTPException(
                        status_code=500,
                        detail="فشل رفع الإيصال إلى التخزين الخاص.",
                    )
            return normalized

        full_path = StorageService._resolve_private_storage_path(normalized)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as file_handle:
            file_handle.write(file_bytes)
        return normalized

    @staticmethod
    async def delete_file(file_key: str) -> None:
        normalized = _validate_private_file_key(file_key)
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            clean_base_url = settings.SUPABASE_URL.rstrip("/")
            url = f"{clean_base_url}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{normalized}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.delete(url, headers=headers)
            return

        full_path = StorageService._resolve_private_storage_path(normalized)
        if os.path.exists(full_path):
            os.remove(full_path)

    @staticmethod
    async def generate_signed_url(file_key: str, expires_in_seconds: int = 300) -> str:
        token = generate_signed_receipt_token(file_key, expires_in_seconds=expires_in_seconds)
        return f"/api/v1/payments/preview?token={token}"

    @staticmethod
    async def get_file_bytes(file_key: str) -> bytes:
        normalized = _validate_private_file_key(file_key)
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            clean_base_url = settings.SUPABASE_URL.rstrip("/")
            url = f"{clean_base_url}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{normalized}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY,
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.content
            raise HTTPException(status_code=404, detail="ملف الإيصال غير موجود.")

        full_path = StorageService._resolve_private_storage_path(normalized)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="ملف الإيصال غير موجود.")
        with open(full_path, "rb") as file_handle:
            return file_handle.read()

    @staticmethod
    def guess_media_type(file_key: str) -> str:
        normalized = _validate_private_file_key(file_key)
        guessed, _ = mimetypes.guess_type(normalized)
        return guessed or "application/octet-stream"
