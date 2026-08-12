from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.db.models import User, Role, UserRole, UserSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Check cookie if header token missing
    if not token:
        cookie_token = request.cookies.get("access_token")
        if cookie_token and cookie_token.startswith("Bearer "):
            token = cookie_token[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="غير مصرح بالدخول. يرجى تسجيل الدخول أولاً."
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="جلسة الدخول منتهية الصلاحية. يرجى إعادة تسجيل الدخول."
        )

    user_id = payload.get("sub")
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="الحساب غير محدد أو تم تعطيله."
        )

    # Session validation is MANDATORY — a JWT without a valid session is rejected
    session_token = request.cookies.get("session_token") or request.headers.get("X-Session-Token")
    if session_token:
        stmt_sess = select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.session_token == session_token,
            UserSession.is_active == True
        )
        res_sess = await db.execute(stmt_sess)
        if not res_sess.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="تم إلغاء هذه الجلسة أو تسجيل الخروج من الأجهزة الأخرى."
            )
    else:
        # If the JWT has a jti but no session token was provided, check if ANY active session exists
        jti = payload.get("jti")
        if jti:
            stmt_any = select(UserSession).where(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).limit(1)
            res_any = await db.execute(stmt_any)
            if not res_any.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="جميع الجلسات منتهية. يرجى إعادة تسجيل الدخول."
                )

    return user

def require_roles(allowed_roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        stmt = select(Role.name).join(UserRole).where(UserRole.user_id == current_user.id)
        res = await db.execute(stmt)
        user_roles = [r for (r,) in res.all()]

        # Super admin overrides
        if "super_admin" in user_roles:
            return current_user

        has_permission = any(r in allowed_roles for r in user_roles)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="عذراً، ليس لديك الصلاحية الكافية للوصول لهذا القسم."
            )
        return current_user
    return role_checker
