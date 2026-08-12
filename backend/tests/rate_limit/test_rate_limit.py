import pytest
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from app.main import app
from app.services.rate_limit_service import ROUTE_LIMITS, get_rate_limit_scope_ip


def _rule_for(method: str, prefix: str):
    for rule_method, rule_prefix, rule in ROUTE_LIMITS:
        if rule_method == method and rule_prefix == prefix:
            return rule
    raise AssertionError(f"Missing rate-limit rule for {method} {prefix}")


def _client(ip_address: str) -> AsyncClient:
    transport = ASGITransport(app=app, client=(ip_address, 54321))
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_forged_x_forwarded_for_cannot_bypass_login_rate_limit():
    rule = _rule_for("POST", "/api/v1/auth/login")
    original_limit = rule.limit
    rule.limit = 2
    try:
        async with _client("198.51.100.10") as client:
            for forwarded_for in ["1.1.1.1", "2.2.2.2"]:
                response = await client.post(
                    "/api/v1/auth/login",
                    json={"identifier": "01099990001", "password": "WrongPassword123!"},
                    headers={"X-Forwarded-For": forwarded_for},
                )
                assert response.status_code == 401

            blocked = await client.post(
                "/api/v1/auth/login",
                json={"identifier": "01099990001", "password": "WrongPassword123!"},
                headers={"X-Forwarded-For": "203.0.113.44"},
            )
            assert blocked.status_code == 429
    finally:
        rule.limit = original_limit


@pytest.mark.asyncio
async def test_forged_x_forwarded_for_cannot_bypass_forgot_password_rate_limit():
    rule = _rule_for("POST", "/api/v1/auth/forgot-password")
    original_limit = rule.limit
    rule.limit = 2
    try:
        async with _client("198.51.100.11") as client:
            for forwarded_for in ["1.1.1.1", "2.2.2.2"]:
                response = await client.post(
                    "/api/v1/auth/forgot-password",
                    json={"identifier": "student1@codejourney.eg"},
                    headers={"X-Forwarded-For": forwarded_for},
                )
                assert response.status_code == 200

            blocked = await client.post(
                "/api/v1/auth/forgot-password",
                json={"identifier": "student1@codejourney.eg"},
                headers={"X-Forwarded-For": "203.0.113.45"},
            )
            assert blocked.status_code == 429
    finally:
        rule.limit = original_limit


@pytest.mark.asyncio
async def test_forged_x_forwarded_for_cannot_bypass_code_run_rate_limit():
    login_rule = _rule_for("POST", "/api/v1/auth/login")
    code_rule = _rule_for("POST", "/api/v1/coding-problems/run")
    original_login_limit = login_rule.limit
    original_code_limit = code_rule.limit
    login_rule.limit = 10
    code_rule.limit = 2
    try:
        async with _client("198.51.100.12") as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"identifier": "01011111111", "password": "StudentPass123!@#"},
            )
            assert login.status_code == 200
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            for forwarded_for in ["1.1.1.1", "2.2.2.2"]:
                response = await client.post(
                    "/api/v1/coding-problems/run",
                    json={"language": "python", "code": 'print("ok")', "stdin": ""},
                    headers={**headers, "X-Forwarded-For": forwarded_for},
                )
                assert response.status_code == 200

            blocked = await client.post(
                "/api/v1/coding-problems/run",
                json={"language": "python", "code": 'print("ok")', "stdin": ""},
                headers={**headers, "X-Forwarded-For": "203.0.113.46"},
            )
            assert blocked.status_code == 429
    finally:
        login_rule.limit = original_login_limit
        code_rule.limit = original_code_limit


@pytest.mark.asyncio
async def test_authenticated_rate_limits_are_scoped_per_user_not_only_per_ip():
    login_rule = _rule_for("POST", "/api/v1/auth/login")
    code_rule = _rule_for("POST", "/api/v1/coding-problems/run")
    original_login_limit = login_rule.limit
    original_code_limit = code_rule.limit
    login_rule.limit = 10
    code_rule.limit = 1
    try:
        async with _client("198.51.100.13") as client:
            first_login = await client.post(
                "/api/v1/auth/login",
                json={"identifier": "01011111111", "password": "StudentPass123!@#"},
            )
            assert first_login.status_code == 200
            first_session_token = first_login.cookies.get("session_token") or ""
            first_headers = {
                "Authorization": f"Bearer {first_login.json()['access_token']}",
                "X-Session-Token": first_session_token,
            }

            second_phone = "01077778888"
            register = await client.post(
                "/api/v1/auth/register",
                json={
                    "arabic_name": "طالب معدل مختلف",
                    "phone_number": second_phone,
                    "password": "StudentPass123",
                    "password_confirm": "StudentPass123",
                    "grade_level": "first_secondary",
                },
            )
            assert register.status_code == 200
            second_session_token = register.cookies.get("session_token") or ""
            second_headers = {
                "Authorization": f"Bearer {register.json()['access_token']}",
                "X-Session-Token": second_session_token,
            }

            client.cookies.set("session_token", first_session_token)
            first_ok = await client.post(
                "/api/v1/coding-problems/run",
                json={"language": "python", "code": 'print("first")', "stdin": ""},
                headers=first_headers,
            )
            assert first_ok.status_code == 200

            client.cookies.set("session_token", second_session_token)
            second_ok = await client.post(
                "/api/v1/coding-problems/run",
                json={"language": "python", "code": 'print("second")', "stdin": ""},
                headers=second_headers,
            )
            assert second_ok.status_code == 200

            client.cookies.set("session_token", first_session_token)
            first_blocked = await client.post(
                "/api/v1/coding-problems/run",
                json={"language": "python", "code": 'print("blocked")', "stdin": ""},
                headers=first_headers,
            )
            assert first_blocked.status_code == 429
    finally:
        login_rule.limit = original_login_limit
        code_rule.limit = original_code_limit


@pytest.mark.asyncio
async def test_trusted_proxy_uses_last_untrusted_hop():
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "headers": [(b"x-forwarded-for", b"10.0.0.2, 203.0.113.20")],
            "client": ("127.0.0.1", 54321),
            "server": ("test", 80),
            "scheme": "http",
            "root_path": "",
            "query_string": b"",
        }
    )
    scope_ip = get_rate_limit_scope_ip(request)
    assert scope_ip == "203.0.113.20"
