import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.db.seed import seed_db, upgrade_schema_to_head

@pytest.fixture(scope="session", autouse=True)
def init_database():
    upgrade_schema_to_head()
    seed_db()

@pytest.fixture(autouse=True)
def reset_user_lockouts():
    from app.core.database import SyncSessionLocal
    from app.db.models import User
    with SyncSessionLocal() as session:
        session.query(User).update({"failed_login_attempts": 0, "locked_until": None})
        session.commit()

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
