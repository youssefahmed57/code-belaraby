import sys
import os
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

TEST_DB_PATH = (Path(tempfile.gettempdir()) / f"code_belaraby_test_suite_{os.getpid()}.db").resolve()
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
                try:
                    candidate.unlink()
                except PermissionError:
                    pass
    upgrade_schema_to_head()
    seed_db()
    yield
    for db_path in _sqlite_test_db_paths():
        for candidate in (db_path, db_path.with_suffix(".db-shm"), db_path.with_suffix(".db-wal"), db_path.with_suffix(".db-journal")):
            if candidate.exists():
                try:
                    candidate.unlink()
                except PermissionError:
                    pass

@pytest.fixture(autouse=True)
def reset_user_lockouts():
    from app.core.database import SyncSessionLocal
    from app.db.models import User
    with SyncSessionLocal() as session:
        session.query(User).update({"failed_login_attempts": 0, "locked_until": None})
        session.commit()


@pytest.fixture(autouse=True)
def reset_auth_throttles():
    from app.services.auth_service import _local_auth_throttle_store

    _local_auth_throttle_store.clear()
    yield
    _local_auth_throttle_store.clear()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    from app.services.rate_limit_service import _local_rate_limit_store

    _local_rate_limit_store.clear()
    yield
    _local_rate_limit_store.clear()


@pytest.fixture(autouse=True)
def reset_cache_state_fixture():
    from app.core.cache import reset_cache_state

    reset_cache_state()
    yield
    reset_cache_state()


@pytest.fixture(autouse=True)
def reset_mock_password_reset_deliveries():
    from app.services.password_reset_delivery_service import clear_mock_password_reset_deliveries

    clear_mock_password_reset_deliveries()
    yield
    clear_mock_password_reset_deliveries()

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
