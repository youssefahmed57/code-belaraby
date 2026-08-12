import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.services.execution_service import ExecutionProviderUnavailable, ExecutionService


@pytest.mark.asyncio
async def test_python_hello_execution(async_client: AsyncClient):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.post(
        "/api/v1/coding-problems/run",
        json={"language": "python", "code": 'print("hello")', "stdin": ""},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Accepted"
    assert response.json()["stdout"].strip() == "hello"


@pytest.mark.asyncio
async def test_python_stdin_execution(async_client: AsyncClient):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.post(
        "/api/v1/coding-problems/run",
        json={"language": "python", "code": 'name = input()\nprint("Hello", name)', "stdin": "Youssef"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Accepted"
    assert response.json()["stdout"].strip() == "Hello Youssef"


@pytest.mark.asyncio
async def test_python_runtime_division_by_zero(async_client: AsyncClient):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.post(
        "/api/v1/coding-problems/run",
        json={"language": "python", "code": "print(1 / 0)", "stdin": ""},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Runtime Error"
    assert "ZeroDivisionError" in response.json()["stderr"]


@pytest.mark.asyncio
async def test_javascript_hello_execution(async_client: AsyncClient):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.post(
        "/api/v1/coding-problems/run",
        json={"language": "javascript", "code": 'console.log("hello world")', "stdin": ""},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Accepted"
    assert response.json()["stdout"].strip() == "hello world"


@pytest.mark.asyncio
async def test_execution_timeout_and_excessive_output(async_client: AsyncClient):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    timeout_response = await async_client.post(
        "/api/v1/coding-problems/run",
        json={"language": "python", "code": "while True: pass", "stdin": ""},
        headers=headers,
    )
    assert timeout_response.status_code == 200
    assert timeout_response.json()["status"] == "Time Limit Exceeded"

    output_response = await async_client.post(
        "/api/v1/coding-problems/run",
        json={"language": "python", "code": "print('A' * 60000)", "stdin": ""},
        headers=headers,
    )
    assert output_response.status_code == 200
    assert "[output truncated at 50KB]" in output_response.json()["stdout"]


@pytest.mark.asyncio
async def test_local_runner_rejected_in_staging_and_production():
    original_environment = settings.ENVIRONMENT
    original_allow = settings.ALLOW_UNSAFE_LOCAL_CODE_EXECUTION
    try:
        settings.ALLOW_UNSAFE_LOCAL_CODE_EXECUTION = False
        for environment in ("staging", "production"):
            settings.ENVIRONMENT = environment
            with pytest.raises(RuntimeError, match="Unsafe local code execution is disabled"):
                ExecutionService.run_code_sync("python", "print('test')")
    finally:
        settings.ENVIRONMENT = original_environment
        settings.ALLOW_UNSAFE_LOCAL_CODE_EXECUTION = original_allow


@pytest.mark.asyncio
async def test_execution_rejects_oversized_source_and_stdin(async_client: AsyncClient):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    oversized_code = "print('x')\n" + ("#" * (settings.MAX_EXECUTION_SOURCE_BYTES + 1))
    oversized_code_response = await async_client.post(
        "/api/v1/coding-problems/run",
        json={"language": "python", "code": oversized_code, "stdin": ""},
        headers=headers,
    )
    assert oversized_code_response.status_code == 413

    oversized_stdin = "a" * (settings.MAX_EXECUTION_STDIN_BYTES + 1)
    oversized_stdin_response = await async_client.post(
        "/api/v1/coding-problems/run",
        json={"language": "python", "code": "print(input())", "stdin": oversized_stdin},
        headers=headers,
    )
    assert oversized_stdin_response.status_code == 413
