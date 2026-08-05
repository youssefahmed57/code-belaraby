import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Request, Response, HTTPException, status
from app.core.config import settings

# CryptContext with Argon2id as primary scheme
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt", "pbkdf2_sha256"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days session

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback simple check or bcrypt format
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None, role: str = "student") -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_csrf_token(session_id: str) -> str:
    message = f"{session_id}:{settings.CSRF_SECRET}"
    return hmac.new(settings.SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()

def verify_csrf_token(session_id: str, csrf_token: str) -> bool:
    expected = generate_csrf_token(session_id)
    return hmac.compare_digest(expected, csrf_token)

def set_auth_cookies(response: Response, access_token: str, session_id: str):
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        expires=60 * 60 * 24 * 7,
        samesite="lax",
        secure=settings.SECURE_COOKIES,
        domain=settings.COOKIE_DOMAIN if settings.COOKIE_DOMAIN != "localhost" else None
    )
    response.set_cookie(
        key="session_token",
        value=session_id,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        expires=60 * 60 * 24 * 7,
        samesite="lax",
        secure=settings.SECURE_COOKIES
    )
    
    csrf_token = generate_csrf_token(session_id)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        max_age=60 * 60 * 24 * 7,
        expires=60 * 60 * 24 * 7,
        samesite="lax",
        secure=settings.SECURE_COOKIES
    )

def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("session_token")
    response.delete_cookie("csrf_token")
