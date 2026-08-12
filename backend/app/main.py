import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.courses import router as courses_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.execution import router as execution_router
from app.api.v1.health import router as health_router
from app.api.v1.lessons import router as lessons_router
from app.api.v1.payments import router as payments_router
from app.api.v1.quizzes import router as quizzes_router
from app.api.v1.settings import router as settings_router
from app.api.v1.videos import router as videos_router
from app.core.config import settings
from app.core.security import verify_csrf_token
from app.services.rate_limit_service import enforce_request_rate_limit


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


is_development_like = settings.is_development_like()
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if is_development_like else None,
    docs_url=f"{settings.API_V1_STR}/docs" if is_development_like else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if is_development_like else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-Token", "X-CSRF-Token"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.SECURE_COOKIES:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            enforce_request_rate_limit(request)
        except Exception as exc:
            if isinstance(exc, JSONResponse):
                return exc
            if isinstance(exc, Exception) and hasattr(exc, "status_code"):
                return JSONResponse(status_code=exc.status_code, content={"detail": getattr(exc, "detail", "Rate limited")})
            raise
        return await call_next(request)


def _origin_allowed(origin: str) -> bool:
    return settings.is_csrf_origin_trusted(origin)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await call_next(request)

        path = request.url.path
        exempt_prefixes = {
            f"{settings.API_V1_STR}/auth/login",
            f"{settings.API_V1_STR}/auth/register",
            f"{settings.API_V1_STR}/auth/forgot-password",
            f"{settings.API_V1_STR}/auth/reset-password",
            "/health",
            "/ready",
        }
        if path in exempt_prefixes:
            return await call_next(request)

        session_token = request.cookies.get("session_token")
        if not session_token:
            return await call_next(request)
        if request.headers.get("authorization"):
            return await call_next(request)

        origin = request.headers.get("origin")
        if origin and not _origin_allowed(origin):
            return JSONResponse(status_code=403, content={"detail": "تم رفض الطلب بسبب Origin غير موثوق."})

        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token or not verify_csrf_token(session_token, csrf_token):
            return JSONResponse(status_code=403, content={"detail": "فشل التحقق من CSRF. يرجى تحديث الصفحة."})

        return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CSRFMiddleware)

try:
    public_assets_dir = os.path.realpath(settings.PUBLIC_ASSETS_LOCAL_DIR)
    os.makedirs(public_assets_dir, exist_ok=True)
    app.mount("/assets", StaticFiles(directory=public_assets_dir), name="public_assets")
except Exception:
    pass


api_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_prefix)
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(courses_router, prefix=api_prefix)
app.include_router(lessons_router, prefix=api_prefix)
app.include_router(payments_router, prefix=api_prefix)
app.include_router(quizzes_router, prefix=api_prefix)
app.include_router(execution_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)
app.include_router(settings_router, prefix=api_prefix)
app.include_router(videos_router, prefix=api_prefix)
app.include_router(health_router, prefix="")
app.include_router(health_router, prefix=api_prefix)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging

    logger = logging.getLogger("uvicorn.error")
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    detail = "حدث خطأ غير متوقع في النظام. يرجى المحاولة لاحقاً."
    if is_development_like:
        detail = f"حدث خطأ غير متوقع في النظام: {exc}"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )
