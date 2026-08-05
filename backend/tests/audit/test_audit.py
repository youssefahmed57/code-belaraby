import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import AuditLog

@pytest.mark.asyncio
async def test_audit_logs_immutability_update_and_delete_prevention(async_session: AsyncSession):
    import uuid
    unique_action = f"TEST_ACTION_{uuid.uuid4().hex}"

    # 1. Create audit log entry
    log_entry = AuditLog(
        action=unique_action,
        entity_type="users",
        entity_id="test_id",
        details={"ip": "127.0.0.1"}
    )
    async_session.add(log_entry)
    await async_session.commit()

    # 2. Attempting to update AuditLog raises PermissionError
    log_entry.action = "MUTATED_ACTION"
    with pytest.raises(PermissionError, match="غير قابل للتعديل"):
        await async_session.commit()
    await async_session.rollback()

    # 3. Fetch fresh entry and attempt to delete AuditLog raises PermissionError
    stmt = select(AuditLog).where(AuditLog.action == unique_action)
    res = await async_session.execute(stmt)
    entry = res.scalars().first()
    assert entry is not None

    await async_session.delete(entry)
    with pytest.raises(PermissionError, match="غير قابل للمسح"):
        await async_session.commit()
    await async_session.rollback()
