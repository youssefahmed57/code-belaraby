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
