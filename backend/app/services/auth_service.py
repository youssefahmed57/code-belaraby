import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

import asyncio
from app.db.models import User, Role, UserRole, UserSession, PasswordResetToken, AuditLog
from app.core.security import get_password_hash, verify_password, create_access_token

EGYPT_PHONE_REGEX = re.compile(r"^01[0125][0-9]{8}$")

def normalize_egypt_phone(phone: str) -> str:
    cleaned = re.sub(r"\D", "", phone)
    if cleaned.startswith("201"):
        cleaned = "0" + cleaned[2:]
    elif cleaned.startswith("00201"):
        cleaned = "0" + cleaned[4:]
    return cleaned

async def get_primary_role(db: AsyncSession, user_id: str) -> str:
    stmt_roles = select(Role.name).join(UserRole).where(UserRole.user_id == user_id)
    res_roles = await db.execute(stmt_roles)
    role_names = [r for (r,) in res_roles.all()]

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
    ip_address: Optional[str] = None
) -> Tuple[User, str]:
    normalized_phone = normalize_egypt_phone(phone_number)
    if not EGYPT_PHONE_REGEX.match(normalized_phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رقم الهاتف المصري غير صحيح. يجب أن يبدأ بـ 010 أو 011 أو 012 أو 015 ويتكون من 11 رقماً."
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور يجب أن تكون 6 أحرف أو أكثر."
        )

    # Check unique phone
    stmt_phone = select(User).where(User.phone_number == normalized_phone)
    res_phone = await db.execute(stmt_phone)
    if res_phone.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رقم الهاتف مسجل بالفعل في المنصة."
        )

    # Check unique email if provided
    if email:
        stmt_email = select(User).where(User.email == email.lower().strip())
        res_email = await db.execute(stmt_email)
        if res_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="البريد الإلكتروني مسجل بالفعل."
            )

    hashed_pw = await asyncio.to_thread(get_password_hash, password)
    new_user = User(
        arabic_name=arabic_name.strip(),
        phone_number=normalized_phone,
        email=email.lower().strip() if email else None,
        hashed_password=hashed_pw,
        grade_level=grade_level,
        parent_name=parent_name.strip() if parent_name else None,
        parent_phone=normalize_egypt_phone(parent_phone) if parent_phone else None,
        status="active"
    )
    db.add(new_user)
    await db.flush()

    # Assign student role
    stmt_role = select(Role).where(Role.name == "student")
    res_role = await db.execute(stmt_role)
    student_role = res_role.scalar_one_or_none()
    if student_role:
        db.add(UserRole(user_id=new_user.id, role_id=student_role.id))

    # Audit log
    db.add(AuditLog(
        user_id=new_user.id,
        action="REGISTER_STUDENT",
        entity_type="users",
        entity_id=new_user.id,
        ip_address=ip_address,
        details={"arabic_name": new_user.arabic_name, "phone": new_user.phone_number}
    ))

    await db.commit()
    await db.refresh(new_user)

    # Create session
    session_token = str(uuid.uuid4())
    user_session = UserSession(
        user_id=new_user.id,
        session_token=session_token,
        ip_address=ip_address,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(user_session)
    await db.commit()

    token = create_access_token(subject=new_user.id, role="student")
    return new_user, token, session_token

async def login_user(
    db: AsyncSession,
    identifier: str, # Phone or email
    password: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Tuple[User, str, str, str]:
    clean_id = identifier.strip()
    norm_phone = normalize_egypt_phone(clean_id)

    stmt = select(User).where((User.phone_number == norm_phone) | (User.email == clean_id.lower()))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رقم الهاتف أو كلمة المرور غير صحيحة."
        )

    # Check if account is currently locked out
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"الحساب مقفل مؤقتاً بسبب محاولات فاشلة متعددة. يرجى المحاولة بعد {remaining} دقيقة."
        )

    # Verify password first (async threadpool offload for high concurrency)
    is_valid_pw = await asyncio.to_thread(verify_password, password, user.hashed_password)
    if not is_valid_pw:
        now = datetime.utcnow()
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="تم تجاوز عدد المحاولات الفاشلة المسموح بها (5 محاولات). تم قفل الحساب مؤقتاً لمدة 15 دقيقة."
            )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رقم الهاتف أو كلمة المرور غير صحيحة."
        )

    # Correct password clears any previous failed attempts or locks
    if (user.failed_login_attempts and user.failed_login_attempts > 0) or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حسابك معطل أو قيد المراجعة. يرجى التواصل مع الدعم الفني."
        )

    primary_role = await get_primary_role(db, user.id)

    session_token = str(uuid.uuid4())
    user_session = UserSession(
        user_id=user.id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(user_session)

    # Audit log
    db.add(AuditLog(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        entity_type="users",
        entity_id=user.id,
        ip_address=ip_address,
        details={"role": primary_role}
    ))

    await db.commit()

    token = create_access_token(subject=user.id, role=primary_role)
    return user, token, session_token, primary_role

async def logout_user(db: AsyncSession, user_id: str, session_token: Optional[str] = None, all_devices: bool = False):
    if all_devices:
        stmt = update(UserSession).where(UserSession.user_id == user_id).values(is_active=False)
    elif session_token:
        stmt = update(UserSession).where(UserSession.session_token == session_token).values(is_active=False)
    else:
        return
    await db.execute(stmt)
    await db.commit()

async def request_password_reset(db: AsyncSession, identifier: str) -> Optional[str]:
    clean_id = identifier.strip()
    norm_phone = normalize_egypt_phone(clean_id)
    stmt = select(User).where((User.phone_number == norm_phone) | (User.email == clean_id.lower()))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        return None

    import hashlib
    raw_token = str(uuid.uuid4())
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    reset_entry = PasswordResetToken(
        user_id=user.id,
        token=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        is_used=False
    )
    db.add(reset_entry)
    await db.commit()
    return raw_token

async def reset_password_with_token(db: AsyncSession, raw_token: str, new_password: str):
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="كلمة المرور الجديدة يجب أن تكون 6 أحرف أو أكثر.")

    import hashlib
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.token == token_hash,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    )
    res = await db.execute(stmt)
    reset_entry = res.scalar_one_or_none()

    if not reset_entry:
        raise HTTPException(status_code=400, detail="رمز إعادة تعيين كلمة المرور غير صالحة أو منتهية الصلاحية.")

    # Update user password & revoke all active sessions
    stmt_u = select(User).where(User.id == reset_entry.user_id)
    res_u = await db.execute(stmt_u)
    user = res_u.scalar_one()

    user.hashed_password = get_password_hash(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    reset_entry.is_used = True

    await logout_user(db, user_id=user.id, all_devices=True)
    await db.commit()
