import os
import time
import hmac
import base64
import hashlib
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.core.config import settings

def generate_signed_receipt_token(file_key: str, expires_in_seconds: int = 300) -> str:
    exp = int(time.time()) + expires_in_seconds
    data = f"{file_key}:{exp}"
    signature = hmac.new(settings.SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()
    raw = f"{data}:{signature}"
    return base64.urlsafe_b64encode(raw.encode()).decode()

def verify_signed_receipt_token(token: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        parts = raw.split(":")
        if len(parts) != 3:
            raise HTTPException(status_code=403, detail="رابط المعاينة غير صالح.")
        file_key, exp_str, signature = parts[0], parts[1], parts[2]
        exp = int(exp_str)
        if time.time() > exp:
            raise HTTPException(status_code=403, detail="انتهت صلاحية رابط المعاينة المؤقت.")
        
        expected_sig = hmac.new(settings.SECRET_KEY.encode(), f"{file_key}:{exp}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(status_code=403, detail="تم التلاعب برابط المعاينة المؤقت.")
        return file_key
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="رمز التوقيع غير صالح.")

class StorageService:
    @staticmethod
    async def upload_file(file_bytes: bytes, file_key: str, content_type: str = "image/png") -> str:
        """
        Uploads payment receipt to Supabase Storage private bucket (payment-receipts).
        Falls back to local file storage if SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set (e.g. offline local unit tests).
        """
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            clean_base_url = settings.SUPABASE_URL.rstrip('/')
            url = f"{clean_base_url}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{file_key}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": content_type,
                "x-upsert": "true"
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, content=file_bytes, headers=headers)
                if res.status_code not in (200, 201):
                    res = await client.put(url, content=file_bytes, headers=headers)
                if res.status_code not in (200, 201):
                    raise HTTPException(
                        status_code=500,
                        detail=f"فشل رفع الإيصال إلى التخزين السحابي (Supabase Storage Error: {res.status_code})"
                    )
            return file_key
        else:
            # Fallback to local storage (for offline unit tests / dev)
            os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
            full_path = os.path.join(settings.STORAGE_LOCAL_DIR, file_key)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file_bytes)
            return file_key

    @staticmethod
    async def generate_signed_url(file_key: str, expires_in_seconds: int = 300) -> str:
        """
        Generates a short-lived signed URL for admin receipt preview.
        Uses Supabase Storage API when configured, or backend signed token fallback.
        """
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            clean_base_url = settings.SUPABASE_URL.rstrip('/')
            url = f"{clean_base_url}/storage/v1/object/sign/{settings.SUPABASE_STORAGE_BUCKET}/{file_key}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": "application/json"
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json={"expiresIn": expires_in_seconds}, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    signed_path = data.get("signedURL")
                    if signed_path:
                        if signed_path.startswith("http"):
                            return signed_path
                        return f"{clean_base_url}/storage/v1{signed_path}"
        # Fallback to backend signed token preview URL
        token = generate_signed_receipt_token(file_key, expires_in_seconds=expires_in_seconds)
        return f"/api/v1/payments/preview?token={token}"

    @staticmethod
    async def get_file_bytes(file_key: str) -> bytes:
        """
        Retrieves file bytes from Supabase Storage or local storage for signed preview endpoint.
        """
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            clean_base_url = settings.SUPABASE_URL.rstrip('/')
            url = f"{clean_base_url}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{file_key}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return res.content
                raise HTTPException(status_code=404, detail="ملف الإيصال غير موجود في التخزين السحابي.")
        else:
            full_path = os.path.join(settings.STORAGE_LOCAL_DIR, file_key)
            if not os.path.exists(full_path):
                raise HTTPException(status_code=404, detail="ملف الإيصال غير موجود.")
            with open(full_path, "rb") as f:
                return f.read()
