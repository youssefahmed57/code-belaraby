import asyncio
import hashlib
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis_client
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models import AuditLog, PasswordResetToken, Role, User, UserRole, UserSession
from app.services.password_reset_delivery_service import (
    PasswordResetDeliveryService,
    PasswordResetDeliveryUnavailable,
)


EGYPT_PHONE_REGEX = re.compile(r"^01[0125][0-9]{8}$")
PASSWORD_DIGIT_REGEX = re.compile(r"\d")
AUTH_THROTTLE_PREFIX = "auth_login_backoff"
_local_auth_throttle_store: dict[str, tuple[int, float, float]] = {}


def normalize_egypt_phone(phone: str) -> str:
    cleaned = re.sub(r"\D", "", phone)
    if cleaned.startswith("201"):
        cleaned = "0" + cleaned[2:]
    elif cleaned.startswith("00201"):
        cleaned = "0" + cleaned[4:]
    return cleaned


def password_policy_error_message() -> str:
    return (
        f"كلمة المرور يجب أن تكون {settings.PASSWORD_MIN_LENGTH} أحرف على الأقل "
        "وتحتوي على رقم واحد على الأقل."
    )


def validate_password_policy(password: str) -> None:
    if len(password or "") < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_policy_error_message())
    if settings.PASSWORD_REQUIRE_DIGIT and not PASSWORD_DIGIT_REGEX.search(password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_policy_error_message())


def _throttle_key(identifier: str) -> str:
    return f"{AUTH_THROTTLE_PREFIX}:{identifier.lower().strip()}"


def _compute_backoff_seconds(failed_attempts: int) -> int:
    if failed_attempts < 5:
        return 0
    return min(900, 30 * (2 ** (failed_attempts - 5)))


def _cleanup_local_throttle_store() -> None:
    now = time.time()
    stale_keys = [key for key, (_, _, expires_at) in _local_auth_throttle_store.items() if expires_at <= now]
    for key in stale_keys:
        _local_auth_throttle_store.pop(key, None)


def _read_throttle_state(identifier: str) -> tuple[int, float]:
    key = _throttle_key(identifier)
    redis_client = get_redis_client()
    if redis_client is not None:
        raw_value = redis_client.get(key)
        if not raw_value:
            return 0, 0.0
        try:
            attempts_text, blocked_until_text = raw_value.split(":", 1)
            return int(attempts_text), float(blocked_until_text)
        except ValueError:
            redis_client.delete(key)
            return 0, 0.0

    _cleanup_local_throttle_store()
    attempts, blocked_until, _ = _local_auth_throttle_store.get(key, (0, 0.0, 0.0))
    return attempts, blocked_until


def _write_throttle_state(identifier: str, failed_attempts: int, blocked_until: float, ttl_seconds: int) -> None:
    key = _throttle_key(identifier)
    redis_client = get_redis_client()
    if redis_client is not None:
        redis_client.setex(key, ttl_seconds, f"{failed_attempts}:{blocked_until}")
        return
    _local_auth_throttle_store[key] = (failed_attempts, blocked_until, time.time() + ttl_seconds)


def clear_auth_throttle(identifier: str) -> None:
    key = _throttle_key(identifier)
    redis_client = get_redis_client()
    if redis_client is not None:
        redis_client.delete(key)
        return
    _local_auth_throttle_store.pop(key, None)


def clear_auth_throttles_for_user(user: User) -> None:
    clear_auth_throttle(user.phone_number)
    if user.email:
        clear_auth_throttle(user.email.lower())


def enforce_login_backoff(identifier: str) -> None:
    _, blocked_until = _read_throttle_state(identifier)
    now = time.time()
    if blocked_until <= now:
        return
    retry_after = max(1, int(blocked_until - now))
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=(
            "تم تأخير محاولات تسجيل الدخول مؤقتاً بسبب تكرار كلمات المرور غير الصحيحة. "
            f"يرجى المحاولة بعد {retry_after} ثانية."
        ),
    )


def record_failed_login(identifier: str) -> None:
    failed_attempts, _ = _read_throttle_state(identifier)
    failed_attempts += 1
    backoff_seconds = _compute_backoff_seconds(failed_attempts)
    blocked_until = time.time() + backoff_seconds if backoff_seconds else 0.0
    _write_throttle_state(identifier, failed_attempts, blocked_until, max(3600, backoff_seconds))


async def get_primary_role(db: AsyncSession, user_id: str) -> str:
    stmt_roles = select(Role.name).join(UserRole).where(UserRole.user_id == user_id)
    res_roles = await db.execute(stmt_roles)
    role_names = [role_name for (role_name,) in res_roles.all()]

    if "super_admin" in role_names:
        return "super_admin"
    if "admin" in role_names:
        return "admin"
    if "instructor" in role_names:
        return "instructor"
    return "student"


async def register_student(
    db: AsyncSession,
    arabic_name: str,
    phone_number: str,
    password: str,
    grade_level: str,
    email: Optional[str] = None,
    parent_name: Optional[str] = None,
    parent_phone: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Tuple[User, str, str]:
    normalized_phone = normalize_egypt_phone(phone_number)
    if not EGYPT_PHONE_REGEX.match(normalized_phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رقم الهاتف المصري غير صحيح. يجب أن يبدأ بـ 010 أو 011 أو 012 أو 015 ويتكون من 11 رقماً.",
        )

    validate_password_policy(password)

    existing_phone = await db.execute(select(User).where(User.phone_number == normalized_phone))
    if existing_phone.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رقم الهاتف مسجل بالفعل في المنصة.")

    normalized_email = email.lower().strip() if email else None
    if normalized_email:
        existing_email = await db.execute(select(User).where(User.email == normalized_email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="البريد الإلكتروني مسجل بالفعل.")

    hashed_password = await asyncio.to_thread(get_password_hash, password)
    new_user = User(
        arabic_name=arabic_name.strip(),
        phone_number=normalized_phone,
        email=normalized_email,
        hashed_password=hashed_password,
        grade_level=grade_level,
        parent_name=parent_name.strip() if parent_name else None,
        parent_phone=normalize_egypt_phone(parent_phone) if parent_phone else None,
        status="active",
    )
    db.add(new_user)
    await db.flush()

    student_role = (await db.execute(select(Role).where(Role.name == "student"))).scalar_one_or_none()
    if student_role:
        db.add(UserRole(user_id=new_user.id, role_id=student_role.id))

    db.add(
        AuditLog(
            user_id=new_user.id,
            action="REGISTER_STUDENT",
            entity_type="users",
            entity_id=new_user.id,
            ip_address=ip_address,
            details={"arabic_name": new_user.arabic_name, "phone": new_user.phone_number},
        )
    )

    await db.commit()
    await db.refresh(new_user)

    session_token = str(uuid.uuid4())
    user_session = UserSession(
        user_id=new_user.id,
        session_token=session_token,
        ip_address=ip_address,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(user_session)
    await db.flush()
    token = create_access_token(subject=new_user.id, role="student", sid=user_session.id)
    await db.commit()

    return new_user, token, session_token


async def login_user(
    db: AsyncSession,
    identifier: str,
    password: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Tuple[User, str, str, str]:
    clean_identifier = identifier.strip()
    normalized_phone = normalize_egypt_phone(clean_identifier)
    normalized_email = clean_identifier.lower()

    result = await db.execute(select(User).where((User.phone_number == normalized_phone) | (User.email == normalized_email)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رقم الهاتف أو كلمة المرور غير صحيحة.")

    throttle_identifier = normalized_email if user.email and normalized_email == user.email.lower() else normalized_phone
    enforce_login_backoff(throttle_identifier)

    is_valid_password = await asyncio.to_thread(verify_password, password, user.hashed_password)
    if not is_valid_password:
        record_failed_login(throttle_identifier)
        enforce_login_backoff(throttle_identifier)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رقم الهاتف أو كلمة المرور غير صحيحة.")

    clear_auth_throttle(throttle_identifier)

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حسابك معطل أو قيد المراجعة. يرجى التواصل مع الدعم الفني.",
        )

    primary_role = await get_primary_role(db, user.id)

    session_token = str(uuid.uuid4())
    user_session = UserSession(
        user_id=user.id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(user_session)
    await db.flush()

    db.add(
        AuditLog(
            user_id=user.id,
            action="LOGIN_SUCCESS",
            entity_type="users",
            entity_id=user.id,
            ip_address=ip_address,
            details={"role": primary_role},
        )
    )

    await db.commit()

    token = create_access_token(subject=user.id, role=primary_role, sid=user_session.id)
    return user, token, session_token, primary_role


async def revoke_user_sessions(
    db: AsyncSession,
    user_id: str,
    session_id: Optional[str] = None,
    all_devices: bool = False,
) -> None:
    if all_devices:
        stmt = update(UserSession).where(UserSession.user_id == user_id).values(is_active=False)
    elif session_id:
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.id == session_id)
            .values(is_active=False)
        )
    else:
        return
    await db.execute(stmt)


async def logout_user(
    db: AsyncSession,
    user_id: str,
    session_id: Optional[str] = None,
    all_devices: bool = False,
) -> None:
    await revoke_user_sessions(db, user_id=user_id, session_id=session_id, all_devices=all_devices)
    await db.commit()


async def request_password_reset(db: AsyncSession, identifier: str) -> bool:
    clean_identifier = identifier.strip()
    normalized_phone = normalize_egypt_phone(clean_identifier)
    normalized_email = clean_identifier.lower()
    result = await db.execute(select(User).where((User.phone_number == normalized_phone) | (User.email == normalized_email)))
    user = result.scalar_one_or_none()
    if not user:
        return False

    raw_token = str(uuid.uuid4())
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    reset_entry = PasswordResetToken(
        user_id=user.id,
        token=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        is_used=False,
    )
    db.add(reset_entry)
    await db.flush()
    try:
        await PasswordResetDeliveryService.deliver_reset_token(user, raw_token)
    except PasswordResetDeliveryUnavailable:
        await db.rollback()
        raise
    await db.commit()
    return True


async def reset_password_with_token(db: AsyncSession, raw_token: str, new_password: str) -> None:
    validate_password_policy(new_password)

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token_hash,
            PasswordResetToken.is_used.is_(False),
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
    )
    reset_entry = result.scalar_one_or_none()
    if not reset_entry:
        raise HTTPException(status_code=400, detail="رمز إعادة تعيين كلمة المرور غير صالح أو منتهي الصلاحية.")

    user = (await db.execute(select(User).where(User.id == reset_entry.user_id))).scalar_one()
    user.hashed_password = get_password_hash(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    reset_entry.is_used = True

    clear_auth_throttles_for_user(user)
    await revoke_user_sessions(db, user_id=user.id, all_devices=True)
    await db.commit()
