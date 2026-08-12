import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from fastapi import Response
import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["argon2", "bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
    argon2__memory_cost=19456,
    argon2__time_cost=2,
    argon2__parallelism=1,
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    role: str = "student",
    sid: Optional[str] = None,
) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
    }
    if sid:
        payload["sid"] = sid
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


def generate_csrf_token(session_id: str) -> str:
    digest = hmac.new(
        settings.CSRF_SECRET.encode("utf-8"),
        session_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest


def verify_csrf_token(session_id: str, csrf_token: str) -> bool:
    return hmac.compare_digest(generate_csrf_token(session_id), csrf_token)


def _cookie_domain() -> Optional[str]:
    if settings.COOKIE_DOMAIN in {"", "localhost"}:
        return None
    return settings.COOKIE_DOMAIN


def set_auth_cookies(response: Response, access_token: str, session_id: str) -> None:
    cookie_kwargs = {
        "max_age": 60 * 60 * 24 * 7,
        "expires": 60 * 60 * 24 * 7,
        "samesite": settings.COOKIE_SAMESITE,
        "secure": settings.SECURE_COOKIES,
        "domain": _cookie_domain(),
        "path": "/",
    }

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        **cookie_kwargs,
    )
    response.set_cookie(
        key="session_token",
        value=session_id,
        httponly=True,
        **cookie_kwargs,
    )
    response.set_cookie(
        key="csrf_token",
        value=generate_csrf_token(session_id),
        httponly=False,
        **cookie_kwargs,
    )


def clear_auth_cookies(response: Response) -> None:
    delete_kwargs = {"domain": _cookie_domain(), "path": "/"}
    response.delete_cookie("access_token", **delete_kwargs)
    response.delete_cookie("session_token", **delete_kwargs)
    response.delete_cookie("csrf_token", **delete_kwargs)
