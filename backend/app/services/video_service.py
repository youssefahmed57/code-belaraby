import time
import hashlib
from typing import Optional, Dict
from jose import jwt
from app.core.config import settings

def mask_phone_number(phone: str) -> str:
    """
    Masks middle digits of phone number for student privacy.
    Example: 01012345678 -> 010***5678
    """
    if not phone or len(phone) < 8:
        return "010***0000"
    return f"{phone[:3]}***{phone[-4:]}"

def generate_student_code(student_id: str) -> str:
    """
    Generates a clean student code badge (e.g. ST-1842) from student_id.
    """
    clean_id = student_id.replace("-", "").upper()
    return f"ST-{clean_id[:4]}"

def generate_bunny_hls_token(video_id: str, expiry_seconds: int = 900) -> Dict[str, str]:
    """
    Generates a secure Signed HLS Token for Bunny Stream Authentication.
    Uses SHA256 signature algorithm required by Bunny Stream Security.
    """
    expires = int(time.time()) + expiry_seconds
    path = f"/{video_id}"
    token_key = settings.BUNNY_STREAM_TOKEN_AUTH_KEY
    
    hashable_string = f"{token_key}{path}{expires}"
    token = hashlib.sha256(hashable_string.encode('utf-8')).hexdigest()
    
    return {
        "token": token,
        "expires": str(expires),
        "library_id": settings.BUNNY_STREAM_LIBRARY_ID,
        "video_id": video_id
    }

def generate_signed_video_token(video_id: str, student_id: str, expiry_minutes: int = 15) -> str:
    """
    Generates a signed JWT playback token for Cloudflare Stream or Dev Video Player.
    Never exposes direct raw video URLs to the browser.
    """
    payload = {
        "sub": video_id,
        "kid": settings.CLOUDFLARE_STREAM_KEY_ID,
        "exp": int(time.time()) + (expiry_minutes * 60),
        "nbf": int(time.time()) - 10,
        "student_id": student_id,
        "student_code": generate_student_code(student_id)
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def get_video_playback_info(video_id: str, student_id: str, student_name: str = "", phone_number: str = "") -> Dict[str, str]:
    token = generate_signed_video_token(video_id, student_id)
    bunny_info = generate_bunny_hls_token(video_id)
    
    masked_phone = mask_phone_number(phone_number)
    student_code = generate_student_code(student_id)

    if settings.USE_MOCK_VIDEO_PROVIDER:
        stream_url = (
            f"/api/v1/videos/stream-mock/{video_id}?"
            f"token={token}&expires={bunny_info['expires']}&"
            f"student_name={student_name}&student_code={student_code}&student_phone={masked_phone}"
        )
    else:
        # Production Bunny Stream Signed HLS Embed URL
        stream_url = (
            f"https://iframe.mediadelivery.net/embed/{bunny_info['library_id']}/{video_id}?"
            f"token={bunny_info['token']}&expires={bunny_info['expires']}&autoplay=true"
        )

    return {
        "video_id": video_id,
        "signed_token": token,
        "hls_signed_token": bunny_info["token"],
        "expires_at": bunny_info["expires"],
        "stream_url": stream_url,
        "provider": "bunny_hls_stream" if not settings.USE_MOCK_VIDEO_PROVIDER else "dev_hls_mock",
        "student_code": student_code,
        "masked_phone": masked_phone
    }
