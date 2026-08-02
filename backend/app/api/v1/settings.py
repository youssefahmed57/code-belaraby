from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models import PlatformSettings, User
from app.api.deps import require_roles

router = APIRouter(prefix="/settings", tags=["Platform Settings"])

@router.get("")
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    stmt = select(PlatformSettings)
    res = await db.execute(stmt)
    settings_rows = res.scalars().all()

    settings_dict = {}
    for row in settings_rows:
        settings_dict[row.key] = row.value

    return settings_dict

@router.post("")
async def update_settings(
    new_settings: Dict[str, Any],
    admin_user: User = Depends(require_roles(["super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    for key, val in new_settings.items():
        stmt = select(PlatformSettings).where(PlatformSettings.key == key)
        res = await db.execute(stmt)
        setting_obj = res.scalar_one_or_none()

        if setting_obj:
            setting_obj.value = val
            setting_obj.updated_by_id = admin_user.id
        else:
            db.add(PlatformSettings(key=key, value=val, updated_by_id=admin_user.id))

    await db.commit()
    return {"message": "تم تحديث إعدادات المنصة بنجاح."}
