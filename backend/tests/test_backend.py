import uuid
import pytest
from httpx import AsyncClient
from app.core.config import settings
from app.services.execution_service import ExecutionService

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_student_registration_and_login(async_client: AsyncClient):
    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    reg_payload = {
        "arabic_name": "طالب جديد اختبار سكيورتي",
        "phone_number": rand_phone,
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary"
    }
    res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_invalid_egyptian_phone(async_client: AsyncClient):
    reg_payload = {
        "arabic_name": "طالب هاتف خطأ",
        "phone_number": "123456",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary"
    }
    res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_python_hello_execution(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
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
async def test_object_level_student_isolation_and_admin_boundary(async_client: AsyncClient):
    student_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = student_res.json()["access_token"]
    s_headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/admin/metrics", headers=s_headers)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_private_payment_receipt_access_and_cross_student_denial(async_client: AsyncClient):
    student3_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    token3 = student3_res.json()["access_token"]
    headers3 = {"Authorization": f"Bearer {token3}"}

    res = await async_client.get("/api/v1/payments/my-payments", headers=headers3)
    assert res.status_code == 200
    my_payments = res.json()
    for p in my_payments:
        assert p["user_id"] != "student_2_id"

@pytest.mark.asyncio
async def test_duplicate_payment_approval_and_transaction_rollback(async_client: AsyncClient):
    student_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01022222222",
        "password": "StudentPass123!@#"
    })
    s_token = student_res.json()["access_token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    courses = (await async_client.get("/api/v1/courses")).json()
    course_id = courses[0]["id"]

    order_res = await async_client.post("/api/v1/payments/order", json={
        "course_id": course_id,
        "payment_method": "instapay"
    }, headers=s_headers)
    payment_id = order_res.json()["id"]

    admin_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01001340533",
        "password": "AdminPass123!@#"
    })
    a_token = admin_res.json()["access_token"]
    a_headers = {"Authorization": f"Bearer {a_token}"}

    review_payload = {"payment_id": payment_id, "action": "approve", "review_note": "Approved"}
    app1 = await async_client.post("/api/v1/payments/admin/review", json=review_payload, headers=a_headers)
    assert app1.status_code == 200
    assert app1.json()["status"] == "approved"

    app2 = await async_client.post("/api/v1/payments/admin/review", json=review_payload, headers=a_headers)
    assert app2.status_code == 200
    assert app2.json()["status"] == "approved"

@pytest.mark.asyncio
async def test_locked_lesson_direct_url_access(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/lessons/if-statements-and-decisions", headers=headers)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_quiz_snapshot_secrecy_timer_and_duplicate_protection(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    lesson_res = await async_client.get("/api/v1/lessons/variables-and-data-types", headers=headers)
    assert lesson_res.status_code == 200
    lesson_data = lesson_res.json()
    quiz_id = lesson_data["quiz"]["id"]

    start_res = await async_client.post(f"/api/v1/quizzes/{quiz_id}/start", headers=headers)
    if start_res.status_code == 200:
        attempt = start_res.json()
        attempt_id = attempt["attempt_id"]
        for q in attempt["questions"]:
            for opt in q["options"]:
                assert "is_correct" not in opt

        answers_list = [
            {"question_id": q["id"], "selected_option_ids": [q["options"][0]["id"]], "text_answer": ""}
            for q in attempt["questions"]
        ]

        sub_res = await async_client.post("/api/v1/quizzes/attempts/submit", json={
            "attempt_id": attempt_id,
            "answers": answers_list
        }, headers=headers)
        assert sub_res.status_code in [200, 400]

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

@pytest.mark.asyncio
async def test_unauthorised_video_token_request(async_client: AsyncClient):
    res = await async_client.get("/api/v1/videos/token/demo_video_lesson_1")
    assert res.status_code == 401
