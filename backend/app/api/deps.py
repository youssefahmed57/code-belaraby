from datetime import datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.db.models import Role, User, UserRole, UserSession


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    cookie_auth_used = False
    if not token:
        cookie_token = request.cookies.get("access_token")
        if cookie_token and cookie_token.startswith("Bearer "):
            token = cookie_token[7:]
            cookie_auth_used = True

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="غير مصرح بالدخول. يرجى تسجيل الدخول أولاً.",
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="جلسة الدخول منتهية الصلاحية. يرجى إعادة تسجيل الدخول.",
        )

    user_id = payload.get("sub")
    session_id = payload.get("sid")
    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="جلسة الدخول غير صالحة. يرجى تسجيل الدخول من جديد.",
        )

    user_session = await db.scalar(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    if (
        not user_session
        or not user_session.is_active
        or (user_session.expires_at and user_session.expires_at <= datetime.utcnow())
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="تم إلغاء هذه الجلسة أو انتهت صلاحيتها. يرجى تسجيل الدخول من جديد.",
        )

    user = await db.scalar(select(User).where(User.id == user_id))
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="الحساب غير محدد أو تم تعطيله.",
        )

    session_token = request.cookies.get("session_token") or request.headers.get("X-Session-Token")
    if cookie_auth_used and not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="جلسة الدخول غير مكتملة. يرجى تسجيل الدخول من جديد.",
        )
    if session_token and session_token != user_session.session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="تم إلغاء هذه الجلسة أو تسجيل الخروج من هذا الجهاز.",
        )

    request.state.session_id = user_session.id
    request.state.session_token = user_session.session_token
    return user


def require_roles(allowed_roles: List[str]):
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        stmt = select(Role.name).join(UserRole).where(UserRole.user_id == current_user.id)
        res = await db.execute(stmt)
        user_roles = [role_name for (role_name,) in res.all()]

        if "super_admin" in user_roles:
            return current_user

        has_permission = any(role_name in allowed_roles for role_name in user_roles)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="عذراً، ليس لديك الصلاحية الكافية للوصول لهذا القسم.",
            )
        return current_user

    return role_checker
