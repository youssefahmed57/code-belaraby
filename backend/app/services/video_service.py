import base64
import hashlib
import hmac
import time
from typing import Any, Dict, Optional

import httpx
import jwt

from app.core.config import settings
from app.db.models import User, VideoAsset


class VideoProviderUnavailable(RuntimeError):
    pass


def mask_phone_number(phone: str) -> str:
    if not phone or len(phone) < 8:
        return "010***0000"
    return f"{phone[:3]}***{phone[-4:]}"


def generate_student_code(student_id: str) -> str:
    clean_id = student_id.replace("-", "").upper()
    return f"ST-{clean_id[:4]}"


def _decode_cloudflare_pem_key() -> str:
    pem_key = settings.CLOUDFLARE_STREAM_PEM_KEY or ""
    if "BEGIN" in pem_key:
        return pem_key
    try:
        return base64.b64decode(pem_key).decode("utf-8")
    except Exception as exc:
        raise VideoProviderUnavailable("Cloudflare Stream signing key is invalid.") from exc


def _build_mock_token(video_id: str, student_id: str, expires_in_seconds: int) -> str:
    expires_at = int(time.time()) + expires_in_seconds
    payload = {
        "sub": video_id,
        "sid": student_id,
        "exp": expires_at,
        "scope": "mock_video_playback",
    }
    return jwt.encode(payload, settings.VIDEO_SIGNING_SECRET, algorithm="HS256")


async def _request_cloudflare_stream_token(video_id: str, expires_in_seconds: int) -> str:
    if not settings.CLOUDFLARE_STREAM_ACCOUNT_ID or not settings.CLOUDFLARE_STREAM_API_TOKEN:
        raise VideoProviderUnavailable("Cloudflare Stream API credentials are unavailable.")

    payload = {
        "exp": int(time.time()) + min(expires_in_seconds, 24 * 60 * 60),
        "nbf": int(time.time()) - 10,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_STREAM_ACCOUNT_ID}/stream/{video_id}/token",
            headers={"Authorization": f"Bearer {settings.CLOUDFLARE_STREAM_API_TOKEN}"},
            json=payload,
        )
    if response.status_code != 200:
        raise VideoProviderUnavailable("Cloudflare Stream token endpoint is unavailable.")
    result = response.json().get("result") or {}
    token = result.get("token")
    if not token:
        raise VideoProviderUnavailable("Cloudflare Stream did not return a playback token.")
    return token


def _sign_cloudflare_stream_token(video_id: str, expires_in_seconds: int) -> str:
    if not settings.CLOUDFLARE_STREAM_KEY_ID or not settings.CLOUDFLARE_STREAM_PEM_KEY:
        raise VideoProviderUnavailable("Cloudflare Stream signing credentials are unavailable.")

    now = int(time.time())
    payload = {
        "sub": video_id,
        "kid": settings.CLOUDFLARE_STREAM_KEY_ID,
        "exp": min(now + expires_in_seconds, now + 24 * 60 * 60),
        "nbf": now - 10,
    }
    headers = {
        "alg": "RS256",
        "kid": settings.CLOUDFLARE_STREAM_KEY_ID,
    }
    return jwt.encode(payload, _decode_cloudflare_pem_key(), algorithm="RS256", headers=headers)


def _generate_bunny_hls_signature(video_id: str, expiry_seconds: int) -> Dict[str, str]:
    if not settings.BUNNY_STREAM_TOKEN_AUTH_KEY or not settings.BUNNY_STREAM_LIBRARY_ID:
        raise VideoProviderUnavailable("Bunny Stream signing credentials are unavailable.")

    expires = int(time.time()) + expiry_seconds
    path = f"/{video_id}"
    signature = hashlib.sha256(
        f"{settings.BUNNY_STREAM_TOKEN_AUTH_KEY}{path}{expires}".encode("utf-8")
    ).hexdigest()
    return {
        "token": signature,
        "expires": str(expires),
        "library_id": settings.BUNNY_STREAM_LIBRARY_ID,
    }


async def get_video_playback_info(
    video_asset: VideoAsset,
    student: User,
    lesson_id: str,
    expires_in_seconds: int = 900,
) -> Dict[str, Any]:
    provider = (video_asset.provider or "").lower()
    masked_phone = mask_phone_number(student.phone_number or "")
    student_code = generate_student_code(student.id)

    if provider == "local":
        if not settings.is_development_like():
            raise VideoProviderUnavailable("Local/mock video playback is disabled outside development and test.")
        token = _build_mock_token(video_asset.id, student.id, expires_in_seconds)
        stream_url = f"/api/v1/videos/stream-mock/{video_asset.id}?lesson_id={lesson_id}&token={token}"
        return {
            "video_id": video_asset.id,
            "provider": "local_mock",
            "stream_url": stream_url,
            "manifest_url": None,
            "player_type": "iframe",
            "expires_at": int(time.time()) + expires_in_seconds,
            "student_code": student_code,
            "masked_phone": masked_phone,
        }

    if provider == "cloudflare_stream":
        if not settings.CLOUDFLARE_STREAM_CUSTOMER_SUBDOMAIN:
            raise VideoProviderUnavailable("Cloudflare Stream playback domain is unavailable.")
        try:
            signed_token = _sign_cloudflare_stream_token(video_asset.external_video_id, expires_in_seconds)
        except VideoProviderUnavailable:
            signed_token = await _request_cloudflare_stream_token(video_asset.external_video_id, expires_in_seconds)

        stream_base = f"https://customer-{settings.CLOUDFLARE_STREAM_CUSTOMER_SUBDOMAIN}.cloudflarestream.com/{signed_token}"
        return {
            "video_id": video_asset.id,
            "provider": provider,
            "stream_url": f"{stream_base}/iframe",
            "manifest_url": f"{stream_base}/manifest/video.m3u8",
            "player_type": "hls",
            "expires_at": int(time.time()) + expires_in_seconds,
            "student_code": student_code,
            "masked_phone": masked_phone,
        }

    if provider == "bunny_stream":
        bunny = _generate_bunny_hls_signature(video_asset.external_video_id, expires_in_seconds)
        base_url = f"https://vz-{bunny['library_id']}.b-cdn.net/{video_asset.external_video_id}"
        return {
            "video_id": video_asset.id,
            "provider": provider,
            "stream_url": f"{base_url}/iframe",
            "manifest_url": f"{base_url}/playlist.m3u8?token={bunny['token']}&expires={bunny['expires']}",
            "player_type": "hls",
            "expires_at": int(bunny["expires"]),
            "student_code": student_code,
            "masked_phone": masked_phone,
        }

    raise VideoProviderUnavailable("No supported video provider is configured for this lesson.")
