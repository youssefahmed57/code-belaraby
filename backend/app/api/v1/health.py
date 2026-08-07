from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter(tags=["Health & Readiness"])

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Code Journey Academy API"}

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(text("SELECT 1"))
        db_status = "connected" if res.scalar() == 1 else "degraded"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        raise HTTPException(status_code=503, detail={"status": "not_ready", "database": db_status})

    return {
        "status": "ready",
        "database": db_status,
        "execution_sandbox": "online"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    import redis
    import httpx
    from app.core.config import settings

    status_report = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "storage": "unknown"
    }

    # 1. Test PostgreSQL DB
    try:
        res = await db.execute(text("SELECT 1"))
        if res.scalar() == 1:
            status_report["database"] = "connected"
        else:
            status_report["database"] = "unresponsive"
    except Exception as e:
        status_report["database"] = f"error: {str(e)}"
        status_report["status"] = "degraded"

    # 2. Test Redis Cache & Queue
    try:
        r_client = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=3.0)
        if r_client.ping():
            status_report["redis"] = "connected"
        else:
            status_report["redis"] = "unresponsive"
    except Exception as e:
        status_report["redis"] = f"error: {str(e)}"
        status_report["status"] = "degraded"

    # 3. Test Supabase Storage
    try:
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/bucket/{settings.SUPABASE_STORAGE_BUCKET}",
                    headers={
                        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                        "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY
                    }
                )
                if res.status_code == 200:
                    status_report["storage"] = "connected (supabase_private_bucket)"
                else:
                    status_report["storage"] = f"bucket_not_found: HTTP {res.status_code}"
                    status_report["status"] = "degraded"
        else:
            status_report["storage"] = "local_fallback"
    except Exception as e:
        status_report["storage"] = f"error: {str(e)}"
        status_report["status"] = "degraded"

    return status_report
