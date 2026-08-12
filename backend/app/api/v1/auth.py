from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import clear_auth_cookies, set_auth_cookies
from app.db.models import User
from app.schemas.all_schemas import LoginRequest, RegisterStudentRequest, TokenResponse, UserResponse
from app.services.auth_service import (
    get_primary_role,
    login_user,
    logout_user,
    register_student,
)
from app.services.password_reset_delivery_service import PasswordResetDeliveryUnavailable
from app.services.rate_limit_service import get_rate_limit_scope_ip


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
async def register(
    req: RegisterStudentRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    if req.password != req.password_confirm:
        raise HTTPException(status_code=400, detail="كلمات المرور غير متطابقة.")

    ip_addr = get_rate_limit_scope_ip(request)
    user, token, session_token = await register_student(
        db=db,
        arabic_name=req.arabic_name,
        phone_number=req.phone_number,
        password=req.password,
        grade_level=req.grade_level,
        email=req.email,
        parent_name=req.parent_name,
        parent_phone=req.parent_phone or req.parent_phone_number,
        ip_address=ip_addr,
    )

    set_auth_cookies(response, token, session_token)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user).model_dump(),
        role="student",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    ip_addr = get_rate_limit_scope_ip(request)
    user_agent = request.headers.get("user-agent")

    user, token, session_token, primary_role = await login_user(
        db=db,
        identifier=req.identifier,
        password=req.password,
        user_agent=user_agent,
        ip_address=ip_addr,
    )

    set_auth_cookies(response, token, session_token)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user).model_dump(),
        role=primary_role,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await logout_user(
        db,
        current_user.id,
        session_id=getattr(request.state, "session_id", None),
        all_devices=False,
    )
    clear_auth_cookies(response)
    return {"message": "تم تسجيل الخروج بنجاح."}


@router.post("/logout-all")
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await logout_user(db, current_user.id, all_devices=True)
    clear_auth_cookies(response)
    return {"message": "تم تسجيل الخروج من جميع الأجهزة بنجاح."}


@router.post("/forgot-password")
async def forgot_password_endpoint(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    identifier = payload.get("identifier", "")
    from app.services.auth_service import request_password_reset

    try:
        await request_password_reset(db, identifier)
    except PasswordResetDeliveryUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="خدمة إعادة تعيين كلمة المرور غير متاحة حالياً.",
        ) from exc
    return {
        "message": "إذا كان البريد الإلكتروني أو رقم الهاتف مسجلاً لدينا، فستتم معالجة الطلب."
    }


@router.post("/reset-password")
async def reset_password_endpoint(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    token = payload.get("token")
    new_password = payload.get("new_password")
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="الرمز وكلمة المرور الجديدة مطلوبان.")

    from app.services.auth_service import reset_password_with_token

    await reset_password_with_token(db, raw_token=token, new_password=new_password)
    return {
        "message": "تم إعادة تعيين كلمة المرور بنجاح. يرجى تسجيل الدخول بكلمة المرور الجديدة."
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response = UserResponse.model_validate(current_user)
    response.role = await get_primary_role(db, current_user.id)
    return response
