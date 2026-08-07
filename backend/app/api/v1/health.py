import datetime
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

@router.get("/status/public")
async def public_status_page(db: AsyncSession = Depends(get_db)):
    import redis
    import time
    from app.core.config import settings

    start_time = time.time()

    # 1. DB latency check
    db_ok = False
    try:
        res = await db.execute(text("SELECT 1"))
        db_ok = (res.scalar() == 1)
    except Exception:
        db_ok = False

    db_latency_ms = round((time.time() - start_time) * 1000, 2)

    # 2. Redis check
    redis_ok = False
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        redis_ok = r.ping()
    except Exception:
        redis_ok = False

    overall_operational = db_ok and redis_ok

    return {
        "platform_name": "كود بالعربي (Code Belaraby)",
        "status": "operational" if overall_operational else "degraded_performance",
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "services": [
            {
                "name": "الواجهة البرمجية (API Services)",
                "status": "operational" if overall_operational else "degraded",
                "latency_ms": db_latency_ms
            },
            {
                "name": "محرر ومحرك التنفيذ (Execution Engine)",
                "status": "operational" if not settings.ALLOW_LOCAL_RUNNER_IN_PROD else "disabled_in_staging",
                "message": "تشغيل الأكواد معطل مؤقتاً لدواعي الأمان في بيئة التجربة" if not settings.ALLOW_LOCAL_RUNNER_IN_PROD else "جاهز"
            },
            {
                "name": "قاعدة البيانات (PostgreSQL Database)",
                "status": "operational" if db_ok else "outage"
            },
            {
                "name": "الذاكرة السريعة وطابور المهام (Redis Cache & Queue)",
                "status": "operational" if redis_ok else "outage"
            }
        ]
    }
