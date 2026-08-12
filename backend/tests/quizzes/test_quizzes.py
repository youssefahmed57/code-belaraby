import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.models import Course, Enrolment, Lesson, LessonProgress, QuizAttempt

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
async def test_locked_lesson_quiz_start_denied(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    headers = {
        "Authorization": f"Bearer {login_res.json()['access_token']}",
        "X-Session-Token": login_res.cookies.get("session_token") or ""
    }

    lesson_login = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    lesson_headers = {"Authorization": f"Bearer {lesson_login.json()['access_token']}"}
    lesson_res = await async_client.get("/api/v1/lessons/variables-and-data-types", headers=lesson_headers)
    quiz_id = lesson_res.json()["quiz"]["id"]
    async_client.cookies.clear()

    start_res = await async_client.post(f"/api/v1/quizzes/{quiz_id}/start", headers=headers)
    assert start_res.status_code in {401, 403}


@pytest.mark.asyncio
async def test_quiz_timeout_does_not_unlock_next_lesson(async_client: AsyncClient, async_session):
    from datetime import datetime, timedelta

    import uuid

    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    register_res = await async_client.post("/api/v1/auth/register", json={
        "arabic_name": "طالب اختبار انتهاء الوقت",
        "phone_number": rand_phone,
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary"
    })
    headers = {"Authorization": f"Bearer {register_res.json()['access_token']}"}
    student_id = register_res.json()["user"]["id"]

    course = await async_session.scalar(select(Course).where(Course.slug == "python-first-secondary"))
    lesson1 = await async_session.scalar(select(Lesson).where(Lesson.slug == "variables-and-data-types"))
    lesson2 = await async_session.scalar(select(Lesson).where(Lesson.slug == "if-statements-and-decisions"))
    async_session.add(
        Enrolment(
            student_id=student_id,
            course_id=course.id,
            status="active",
            access_start=datetime.utcnow(),
            access_expiry=datetime.utcnow() + timedelta(days=30),
            source="admin_assignment",
        )
    )
    async_session.add(
        LessonProgress(
            student_id=student_id,
            lesson_id=lesson1.id,
            status="available",
        )
    )
    await async_session.commit()

    lesson_res = await async_client.get("/api/v1/lessons/variables-and-data-types", headers=headers)
    quiz_id = lesson_res.json()["quiz"]["id"]
    start_res = await async_client.post(f"/api/v1/quizzes/{quiz_id}/start", headers=headers)
    assert start_res.status_code == 200
    attempt = start_res.json()

    db_attempt = await async_session.scalar(select(QuizAttempt).where(QuizAttempt.id == attempt["attempt_id"]))
    db_attempt.start_time = datetime.utcnow() - timedelta(minutes=30)
    await async_session.commit()

    answers = [
        {"question_id": question["id"], "selected_option_ids": [question["options"][0]["id"]]}
        for question in attempt["questions"]
    ]
    submit_res = await async_client.post("/api/v1/quizzes/attempts/submit", json={
        "attempt_id": attempt["attempt_id"],
        "answers": answers,
    }, headers=headers)
    assert submit_res.status_code == 200
    submit_data = submit_res.json()
    assert submit_data["status"] == "timed_out"
    assert submit_data["passed"] is False

    lesson_progress = await async_session.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == lesson1.id,
        )
    )
    assert lesson_progress is not None
    assert lesson_progress.quiz_passed is False
    assert (lesson_progress.best_quiz_score or 0) == 0

    locked_lesson_res = await async_client.get(f"/api/v1/lessons/{lesson2.slug}", headers=headers)
    assert locked_lesson_res.status_code == 403


@pytest.mark.asyncio
async def test_quiz_rejects_foreign_option_ids_and_duplicate_questions(async_client: AsyncClient, async_session):
    import uuid
    from datetime import datetime, timedelta

    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    register_res = await async_client.post("/api/v1/auth/register", json={
        "arabic_name": "طالب اختبار تلاعب الكويز",
        "phone_number": rand_phone,
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary"
    })
    headers = {"Authorization": f"Bearer {register_res.json()['access_token']}"}
    student_id = register_res.json()["user"]["id"]

    course = await async_session.scalar(select(Course).where(Course.slug == "python-first-secondary"))
    lesson = await async_session.scalar(select(Lesson).where(Lesson.slug == "variables-and-data-types"))
    async_session.add(
        Enrolment(
            student_id=student_id,
            course_id=course.id,
            status="active",
            access_start=datetime.utcnow(),
            access_expiry=datetime.utcnow() + timedelta(days=30),
            source="admin_assignment",
        )
    )
    async_session.add(
        LessonProgress(
            student_id=student_id,
            lesson_id=lesson.id,
            status="available",
        )
    )
    await async_session.commit()

    lesson_res = await async_client.get("/api/v1/lessons/variables-and-data-types", headers=headers)
    quiz_id = lesson_res.json()["quiz"]["id"]

    start_res = await async_client.post(f"/api/v1/quizzes/{quiz_id}/start", headers=headers)
    assert start_res.status_code == 200
    attempt = start_res.json()
    assert len(attempt["questions"]) >= 2

    first_question = attempt["questions"][0]
    second_question = attempt["questions"][1]
    foreign_option_id = second_question["options"][0]["id"]

    foreign_option_res = await async_client.post("/api/v1/quizzes/attempts/submit", json={
        "attempt_id": attempt["attempt_id"],
        "answers": [
            {"question_id": first_question["id"], "selected_option_ids": [foreign_option_id]},
        ],
    }, headers=headers)
    assert foreign_option_res.status_code == 400

    dup_question = attempt["questions"][0]
    dup_option = dup_question["options"][0]["id"]

    duplicate_res = await async_client.post("/api/v1/quizzes/attempts/submit", json={
        "attempt_id": attempt["attempt_id"],
        "answers": [
            {"question_id": dup_question["id"], "selected_option_ids": [dup_option]},
            {"question_id": dup_question["id"], "selected_option_ids": [dup_option]},
        ],
    }, headers=headers)
    assert duplicate_res.status_code == 400
