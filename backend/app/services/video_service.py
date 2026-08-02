import time
from typing import Optional, Dict
from jose import jwt
from app.core.config import settings

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
        "watermark_text": f"Student ID: {student_id[:8]}"
    }
    
    # In production, use private RSA key. In dev/mock mode, sign with HS256 using SECRET_KEY.
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def get_video_playback_info(video_id: str, student_id: str) -> Dict[str, str]:
    token = generate_signed_video_token(video_id, student_id)
    if settings.USE_MOCK_VIDEO_PROVIDER:
        # Returns a dev video streamer endpoint
        stream_url = f"/api/v1/videos/stream-mock/{video_id}?token={token}"
    else:
        stream_url = f"https://iframe.videodelivery.net/{video_id}?token={token}"

    return {
        "video_id": video_id,
        "signed_token": token,
        "stream_url": stream_url,
        "provider": "cloudflare_stream" if not settings.USE_MOCK_VIDEO_PROVIDER else "dev_mock"
    }
