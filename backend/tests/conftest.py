import sys
import os
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

TEST_DB_PATH = (Path(__file__).resolve().parents[1] / "test_suite.db").resolve()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SYNC_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.config import settings
from app.db.seed import seed_db, upgrade_schema_to_head


def _sqlite_test_db_paths() -> list[Path]:
    candidates = {TEST_DB_PATH}
    for url in {settings.DATABASE_URL, settings.SYNC_DATABASE_URL}:
        normalized = url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        if normalized and not normalized.startswith("postgresql"):
            candidates.add(Path(normalized).resolve())
    return list(candidates)


@pytest.fixture(scope="session", autouse=True)
def init_database():
    for db_path in _sqlite_test_db_paths():
        for candidate in (db_path, db_path.with_suffix(".db-shm"), db_path.with_suffix(".db-wal"), db_path.with_suffix(".db-journal")):
            if candidate.exists():
                candidate.unlink()
    upgrade_schema_to_head()
    seed_db()

@pytest.fixture(autouse=True)
def reset_user_lockouts():
    from app.core.database import SyncSessionLocal
    from app.db.models import User
    with SyncSessionLocal() as session:
        session.query(User).update({"failed_login_attempts": 0, "locked_until": None})
        session.commit()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    from app.services.rate_limit_service import _local_rate_limit_store

    _local_rate_limit_store.clear()
    yield
    _local_rate_limit_store.clear()

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture
async def async_session():
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session
