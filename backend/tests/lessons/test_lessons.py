import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.models import CodingProblem, Course, Enrolment, Lesson, LessonProgress


@pytest.mark.asyncio
async def test_locked_lesson_direct_url_access(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = await async_client.get("/api/v1/lessons/if-statements-and-decisions", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_unauthorised_video_token_request(async_client: AsyncClient):
    res = await async_client.get("/api/v1/videos/token/demo_video_lesson_1")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_summary_enrolment_filters_and_progress_isolation(async_client: AsyncClient):
    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    reg_payload = {
        "arabic_name": "طالب لاختبار اللوحة",
        "phone_number": rand_phone,
        "password": "Password123!",
        "password_confirm": "Password123!",
        "grade_level": "first_secondary"
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    dash0 = await async_client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash0.status_code == 200
    data0 = dash0.json()
    assert data0["active_enrolment_count"] == 0
    assert len(data0["courses"]) == 0
    assert len(data0["suggested_courses"]) >= 1

    s3_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    h3 = {"Authorization": f"Bearer {s3_res.json()['access_token']}"}

    dash3 = await async_client.get("/api/v1/dashboard/summary", headers=h3)
    assert dash3.status_code == 200
    data3 = dash3.json()
    assert data3["active_enrolment_count"] == len(data3["courses"])


@pytest.mark.asyncio
async def test_locked_lesson_complete_theory_denied(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    complete_res = await async_client.post("/api/v1/lessons/if-statements-and-decisions/complete-theory", headers=headers)
    assert complete_res.status_code == 403


@pytest.mark.asyncio
async def test_locked_lesson_video_progress_denied(async_client: AsyncClient):
    student3_login = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    student3_headers = {
        "Authorization": f"Bearer {student3_login.json()['access_token']}",
        "X-Session-Token": student3_login.cookies.get("session_token") or ""
    }

    student1_login = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    student1_headers = {
        "Authorization": f"Bearer {student1_login.json()['access_token']}",
        "X-Session-Token": student1_login.cookies.get("session_token") or ""
    }
    lesson1 = (await async_client.get("/api/v1/lessons/variables-and-data-types", headers=student1_headers)).json()
    async_client.cookies.clear()

    progress_res = await async_client.post("/api/v1/videos/progress", json={
        "lesson_id": lesson1["id"],
        "video_id": lesson1["video_asset_id"],
        "current_position": 10,
        "duration": 100
    }, headers=student3_headers)
    assert progress_res.status_code == 403


@pytest.mark.asyncio
async def test_video_progress_rejects_fake_first_completion(async_client: AsyncClient):
    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01011111111",
        "password": "StudentPass123!@#"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    lesson_res = await async_client.get("/api/v1/lessons/variables-and-data-types", headers=headers)
    lesson = lesson_res.json()

    progress_res = await async_client.post("/api/v1/videos/progress", json={
        "lesson_id": lesson["id"],
        "video_id": lesson["video_asset_id"],
        "current_position": 100,
        "duration": 100
    }, headers=headers)
    assert progress_res.status_code == 400


@pytest.mark.asyncio
async def test_video_progress_rejects_impossible_jump(async_client: AsyncClient, async_session):
    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    register_res = await async_client.post("/api/v1/auth/register", json={
        "arabic_name": "طالب اختبار تقدم الفيديو",
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

    first_progress = await async_client.post("/api/v1/videos/progress", json={
        "lesson_id": lesson.id,
        "video_id": lesson.video_asset_id,
        "current_position": 10,
        "duration": 100
    }, headers=headers)
    assert first_progress.status_code == 200

    jumped_progress = await async_client.post("/api/v1/videos/progress", json={
        "lesson_id": lesson.id,
        "video_id": lesson.video_asset_id,
        "current_position": 95,
        "duration": 100
    }, headers=headers)
    assert jumped_progress.status_code == 400


@pytest.mark.asyncio
async def test_locked_lesson_coding_submit_denied(async_client: AsyncClient, async_session):
    problem = await async_session.scalar(
        select(CodingProblem).join(Lesson, CodingProblem.lesson_id == Lesson.id).where(Lesson.slug == "variables-and-data-types")
    )
    assert problem is not None

    login_res = await async_client.post("/api/v1/auth/login", json={
        "identifier": "01033333333",
        "password": "StudentPass123!@#"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    submit_res = await async_client.post("/api/v1/coding-problems/submit", json={
        "problem_id": problem.id,
        "lesson_id": "fake-other-lesson-id",
        "language": "python",
        "code": "daily = int(input())\nprint(f'Total: {daily * 7}')",
    }, headers=headers)
    assert submit_res.status_code == 403


@pytest.mark.asyncio
async def test_problem_submit_cannot_spoof_lesson_progress(async_client: AsyncClient, async_session):
    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    register_res = await async_client.post("/api/v1/auth/register", json={
        "arabic_name": "طالب اختبار تزوير الدرس",
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
    problem = await async_session.scalar(select(CodingProblem).where(CodingProblem.lesson_id == lesson1.id))
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

    assert lesson1 is not None
    assert lesson2 is not None
    assert problem is not None

    submit_res = await async_client.post("/api/v1/coding-problems/submit", json={
        "problem_id": problem.id,
        "lesson_id": lesson2.id,
        "language": "python",
        "code": "daily = int(input())\nprint(f'Total: {daily * 7}')",
    }, headers=headers)
    assert submit_res.status_code == 200

    locked_lesson_res = await async_client.get(f"/api/v1/lessons/{lesson2.slug}", headers=headers)
    assert locked_lesson_res.status_code == 403

    spoofed_progress = await async_session.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == lesson2.id,
        )
    )
    assert spoofed_progress is None
