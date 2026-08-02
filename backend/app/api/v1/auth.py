from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import set_auth_cookies, clear_auth_cookies
from app.schemas.all_schemas import RegisterStudentRequest, LoginRequest, UserResponse, TokenResponse
from app.services.auth_service import register_student, login_user, logout_user
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=TokenResponse)
async def register(
    req: RegisterStudentRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    if req.password != req.password_confirm:
        raise HTTPException(status_code=400, detail="كلمات المرور غير متطابقة.")

    ip_addr = request.client.host if request.client else None
    user, token = await register_student(
        db=db,
        arabic_name=req.arabic_name,
        phone_number=req.phone_number,
        password=req.password,
        grade_level=req.grade_level,
        email=req.email,
        parent_name=req.parent_name,
        parent_phone=req.parent_phone or req.parent_phone_number,
        ip_address=ip_addr
    )

    set_auth_cookies(response, token, user.id)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user).model_dump(),
        role="student"
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    ip_addr = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, token, session_token, primary_role = await login_user(
        db=db,
        identifier=req.identifier,
        password=req.password,
        user_agent=user_agent,
        ip_address=ip_addr
    )

    set_auth_cookies(response, token, session_token)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user).model_dump(),
        role=primary_role
    )

@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await logout_user(db, current_user.id, all_devices=False)
    clear_auth_cookies(response)
    return {"message": "تم تسجيل الخروج بنجاح."}
