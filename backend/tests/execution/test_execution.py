import pytest
from httpx import AsyncClient
from app.core.config import settings
from app.services.execution_service import ExecutionService

@pytest.mark.asyncio
async def test_python_hello_execution(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    print("LOGIN RES:", login_res.status_code, login_res.json())
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.post("/api/v1/coding-problems/run", json={
        "language": "python",
        "code": 'print("hello")',
        "stdin": ""
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Accepted"
    assert data["stdout"].strip() == "hello"

@pytest.mark.asyncio
async def test_python_stdin_execution(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.post("/api/v1/coding-problems/run", json={
        "language": "python",
        "code": 'name = input()\nprint("Hello", name)',
        "stdin": "Youssef"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Accepted"
    assert data["stdout"].strip() == "Hello Youssef"

@pytest.mark.asyncio
async def test_python_runtime_division_by_zero(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.post("/api/v1/coding-problems/run", json={
        "language": "python",
        "code": 'print(1 / 0)',
        "stdin": ""
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Runtime Error"
    assert "ZeroDivisionError" in data["stderr"]

@pytest.mark.asyncio
async def test_execution_timeout_and_excessive_output(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    timeout_res = await async_client.post("/api/v1/coding-problems/run", json={
        "language": "python",
        "code": "while True: pass",
        "stdin": ""
    }, headers=headers)
    assert timeout_res.status_code == 200
    assert timeout_res.json()["status"] == "Time Limit Exceeded"

    excess_res = await async_client.post("/api/v1/coding-problems/run", json={
        "language": "python",
        "code": "print('A' * 60000)",
        "stdin": ""
    }, headers=headers)
    assert excess_res.status_code == 200
    assert "تم اقتطاع المخرجات المفرطة" in excess_res.json()["stdout"]

@pytest.mark.asyncio
async def test_production_local_runner_rejection():
    original_env = settings.ENVIRONMENT
    original_allow = settings.ALLOW_LOCAL_RUNNER_IN_PROD
    try:
        settings.ENVIRONMENT = "production"
        settings.ALLOW_LOCAL_RUNNER_IN_PROD = False
        with pytest.raises(RuntimeError, match="disabled in production environment"):
            ExecutionService.run_code_sync("python", "print('test')")
    finally:
        settings.ENVIRONMENT = original_env
        settings.ALLOW_LOCAL_RUNNER_IN_PROD = original_allow
