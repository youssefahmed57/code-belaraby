import datetime

import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.services.execution_service import ExecutionService


router = APIRouter(tags=["Health & Readiness"])


async def _database_ready(db: AsyncSession) -> bool:
    result = await db.execute(text("SELECT 1"))
    return result.scalar() == 1


def _redis_ready() -> bool:
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        return bool(client.ping())
    except Exception:
        return False


@router.get("/health")
async def health_check():
    return {"status": "alive", "service": "Code Belaraby API"}


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    db_ok = False
    try:
        db_ok = await _database_ready(db)
    except Exception:
        db_ok = False

    execution_health = await ExecutionService.check_execution_provider_health()
    execution_required = settings.requires_isolated_code_execution()
    execution_ok = (not execution_required) or execution_health["healthy"]

    if not db_ok or not execution_ok:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "ready" if db_ok else "unavailable",
                "execution": "ready" if execution_ok else "unavailable",
            },
        )

    return {
        "status": "ready",
        "database": "ready",
        "execution": "ready" if execution_health["healthy"] else "not_required",
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    try:
        db_ok = await _database_ready(db)
    except Exception:
        db_ok = False

    redis_ok = _redis_ready()
    execution_health = await ExecutionService.check_execution_provider_health()
    storage_ok = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY) or settings.is_development_like()
    password_reset_delivery_ok = settings.is_password_reset_delivery_configured()

    overall_ok = db_ok and redis_ok and (
        execution_health["healthy"] or not settings.requires_isolated_code_execution()
    )
    return {
        "status": "healthy" if overall_ok else "degraded",
        "checks": {
            "database": "connected" if db_ok else "unavailable",
            "redis": "connected" if redis_ok else "unavailable",
            "storage": "configured" if storage_ok else "unavailable",
            "execution_provider": "connected" if execution_health["healthy"] else "unavailable",
            "password_reset_delivery": "configured" if password_reset_delivery_ok else "unavailable",
        },
    }


@router.get("/status/public")
async def public_status_page(db: AsyncSession = Depends(get_db)):
    try:
        db_ok = await _database_ready(db)
    except Exception:
        db_ok = False

    redis_ok = _redis_ready()
    execution_health = await ExecutionService.check_execution_provider_health()
    execution_required = settings.requires_isolated_code_execution()
    execution_ok = execution_health["healthy"] if execution_required else True

    overall_operational = db_ok and redis_ok and execution_ok
    return {
        "platform_name": "كود بالعربي (Code Belaraby)",
        "status": "operational" if overall_operational else "degraded",
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "services": [
            {
                "name": "واجهة المنصة",
                "status": "operational" if db_ok else "degraded",
            },
            {
                "name": "محرك تشغيل الأكواد",
                "status": "operational" if execution_ok else "degraded",
            },
            {
                "name": "قاعدة البيانات",
                "status": "operational" if db_ok else "degraded",
            },
            {
                "name": "الذاكرة المؤقتة والطوابير",
                "status": "operational" if redis_ok else "degraded",
            },
        ],
    }
