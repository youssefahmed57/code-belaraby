import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models import (
    CodingProblem,
    Course,
    Enrolment,
    Lesson,
    LessonPrerequisite,
    LessonProgress,
    Module,
    User,
    VideoProgress,
)
from app.services.access_service import check_lesson_access


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


async def _create_progression_fixture(async_session):
    suffix = uuid.uuid4().hex[:8]
    student = User(
        arabic_name=f"طالب صلاحيات {suffix}",
        phone_number=f"010{uuid.uuid4().int % 100000000:08d}",
        email=f"progress-{suffix}@codebelaraby.test",
        hashed_password=get_password_hash("Password123!"),
        grade_level="first_secondary",
        status="active",
    )
    course = Course(
        title=f"Course {suffix}",
        slug=f"course-{suffix}",
        short_description="Synthetic course",
        full_description="Synthetic course for access control tests",
        grade_level="first_secondary",
        price=0,
        status="published",
        visibility="public",
        unlock_mode="sequential",
    )
    async_session.add_all([student, course])
    await async_session.flush()

    modules = [
        Module(course_id=course.id, title=f"Module {index}", order=index, status="published")
        for index in (1, 2, 3)
    ]
    async_session.add_all(modules)
    await async_session.flush()

    lessons = [
        Lesson(module_id=modules[0].id, title="M1L1", slug=f"m1l1-{suffix}", order=1, publishing_status="published"),
        Lesson(module_id=modules[0].id, title="M1L2", slug=f"m1l2-{suffix}", order=2, publishing_status="published"),
        Lesson(module_id=modules[1].id, title="M2L1", slug=f"m2l1-{suffix}", order=1, publishing_status="published"),
        Lesson(module_id=modules[2].id, title="M3L1", slug=f"m3l1-{suffix}", order=1, publishing_status="published"),
    ]
    async_session.add_all(lessons)
    await async_session.flush()

    enrolment = Enrolment(
        student_id=student.id,
        course_id=course.id,
        status="active",
        access_start=datetime.utcnow() - timedelta(days=1),
        access_expiry=datetime.utcnow() + timedelta(days=30),
        source="admin_assignment",
    )
    async_session.add(enrolment)
    await async_session.commit()

    return {
        "student": student,
        "course": course,
        "modules": modules,
        "lessons": lessons,
        "enrolment": enrolment,
    }


async def _mark_completed(async_session, student_id: str, lesson_id: str, manual_override: bool = False):
    progress = await async_session.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    if not progress:
        progress = LessonProgress(
            student_id=student_id,
            lesson_id=lesson_id,
            status="completed",
            manual_override=manual_override,
        )
        async_session.add(progress)
    else:
        progress.status = "completed"
        progress.manual_override = manual_override
    await async_session.commit()


@pytest.mark.asyncio
async def test_lesson_access_progression_blocks_module_bypass(async_session):
    fixture = await _create_progression_fixture(async_session)
    student = fixture["student"]
    lesson1, lesson2, lesson3, _lesson4 = fixture["lessons"]

    assert await check_lesson_access(async_session, student.id, lesson1.id) is True
    assert await check_lesson_access(async_session, student.id, lesson2.id) is False
    assert await check_lesson_access(async_session, student.id, lesson3.id) is False

    await _mark_completed(async_session, student.id, lesson1.id)
    assert await check_lesson_access(async_session, student.id, lesson2.id) is True
    assert await check_lesson_access(async_session, student.id, lesson3.id) is False

    await _mark_completed(async_session, student.id, lesson2.id)
    assert await check_lesson_access(async_session, student.id, lesson3.id) is True


@pytest.mark.asyncio
async def test_lesson_access_respects_explicit_prerequisites(async_session):
    fixture = await _create_progression_fixture(async_session)
    student = fixture["student"]
    lesson1, _lesson2, lesson3, lesson4 = fixture["lessons"]

    async_session.add(LessonPrerequisite(lesson_id=lesson4.id, prerequisite_lesson_id=lesson1.id))
    await async_session.commit()

    assert await check_lesson_access(async_session, student.id, lesson4.id) is False
    await _mark_completed(async_session, student.id, lesson1.id)
    assert await check_lesson_access(async_session, student.id, lesson4.id) is True
    assert await check_lesson_access(async_session, student.id, lesson3.id) is False


@pytest.mark.asyncio
async def test_unpublished_modules_and_prerequisites_do_not_unlock_or_block(async_session):
    fixture = await _create_progression_fixture(async_session)
    student = fixture["student"]
    lesson1, lesson2, lesson3, _lesson4 = fixture["lessons"]
    unpublished_module = Module(
        course_id=fixture["course"].id,
        title="Hidden module",
        order=99,
        status="draft",
    )
    async_session.add(unpublished_module)
    await async_session.flush()
    hidden_lesson = Lesson(
        module_id=unpublished_module.id,
        title="Hidden lesson",
        slug=f"hidden-{uuid.uuid4().hex[:8]}",
        order=1,
        publishing_status="published",
    )
    async_session.add(hidden_lesson)
    await async_session.flush()
    async_session.add(LessonPrerequisite(lesson_id=lesson3.id, prerequisite_lesson_id=hidden_lesson.id))
    await async_session.commit()

    assert await check_lesson_access(async_session, student.id, lesson3.id) is False
    await _mark_completed(async_session, student.id, lesson1.id)
    await _mark_completed(async_session, student.id, lesson2.id)
    assert await check_lesson_access(async_session, student.id, lesson3.id) is True


@pytest.mark.asyncio
async def test_manual_override_grants_access_but_expired_enrolment_still_denies(async_session):
    fixture = await _create_progression_fixture(async_session)
    student = fixture["student"]
    _lesson1, _lesson2, _lesson3, lesson4 = fixture["lessons"]

    progress = LessonProgress(
        student_id=student.id,
        lesson_id=lesson4.id,
        status="available",
        manual_override=True,
    )
    async_session.add(progress)
    await async_session.commit()
    assert await check_lesson_access(async_session, student.id, lesson4.id) is True

    fixture["enrolment"].access_expiry = datetime.utcnow() - timedelta(minutes=1)
    await async_session.commit()
    assert await check_lesson_access(async_session, student.id, lesson4.id) is False


@pytest.mark.asyncio
async def test_video_progress_uses_authoritative_duration(async_client: AsyncClient, async_session):
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    lesson = (await async_client.get("/api/v1/lessons/variables-and-data-types", headers=headers)).json()

    response = await async_client.post(
        "/api/v1/videos/progress",
        json={
            "lesson_id": lesson["id"],
            "video_id": lesson["video_asset_id"],
            "current_position": 30,
            "duration": 30,
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["watched_percentage"] == 5.0
    assert response.json()["lesson_completed"] is False


@pytest.mark.asyncio
async def test_video_progress_seeking_backwards_does_not_add_fake_watch_time(async_client: AsyncClient, async_session):
    rand_phone = f"010{uuid.uuid4().int % 100000000:08d}"
    register_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "arabic_name": "طالب مشاهدة طبيعية",
            "phone_number": rand_phone,
            "password": "Password123!",
            "password_confirm": "Password123!",
            "grade_level": "first_secondary",
        },
    )
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
    async_session.add(LessonProgress(student_id=student_id, lesson_id=lesson.id, status="available"))
    await async_session.commit()

    first = await async_client.post(
        "/api/v1/videos/progress",
        json={"lesson_id": lesson.id, "video_id": lesson.video_asset_id, "current_position": 20, "duration": 20},
        headers=headers,
    )
    assert first.status_code == 200

    progress = await async_session.scalar(
        select(VideoProgress).where(
            VideoProgress.student_id == student_id,
            VideoProgress.lesson_id == lesson.id,
            VideoProgress.video_asset_id == lesson.video_asset_id,
        )
    )
    progress.last_watched_at = datetime.utcnow() - timedelta(minutes=2)
    await async_session.commit()

    second = await async_client.post(
        "/api/v1/videos/progress",
        json={"lesson_id": lesson.id, "video_id": lesson.video_asset_id, "current_position": 80, "duration": 80},
        headers=headers,
    )
    assert second.status_code == 200

    progress = await async_session.scalar(
        select(VideoProgress).where(
            VideoProgress.student_id == student_id,
            VideoProgress.lesson_id == lesson.id,
            VideoProgress.video_asset_id == lesson.video_asset_id,
        )
    )
    await async_session.refresh(progress)
    watched_before_seek = progress.total_watched_seconds
    progress.last_watched_at = datetime.utcnow() - timedelta(minutes=2)
    await async_session.commit()

    seek_back = await async_client.post(
        "/api/v1/videos/progress",
        json={"lesson_id": lesson.id, "video_id": lesson.video_asset_id, "current_position": 40, "duration": 40},
        headers=headers,
    )
    assert seek_back.status_code == 200

    progress = await async_session.scalar(
        select(VideoProgress).where(
            VideoProgress.student_id == student_id,
            VideoProgress.lesson_id == lesson.id,
            VideoProgress.video_asset_id == lesson.video_asset_id,
        )
    )
    await async_session.refresh(progress)
    assert progress.total_watched_seconds == watched_before_seek
    assert progress.session_count >= 2


@pytest.mark.asyncio
async def test_video_progress_shared_across_multiple_sessions_and_completion_threshold(async_client: AsyncClient, async_session):
    first_login = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    first_headers = {"Authorization": f"Bearer {first_login.json()['access_token']}"}

    second_login = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    second_headers = {"Authorization": f"Bearer {second_login.json()['access_token']}"}

    lesson = await async_session.scalar(select(Lesson).where(Lesson.slug == "variables-and-data-types"))
    student = await async_session.scalar(select(User).where(User.phone_number == "01011111111"))
    lesson_progress = await async_session.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == student.id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    if not lesson_progress:
        lesson_progress = LessonProgress(student_id=student.id, lesson_id=lesson.id, status="available")
        async_session.add(lesson_progress)

    progress = await async_session.scalar(
        select(VideoProgress).where(
            VideoProgress.student_id == student.id,
            VideoProgress.lesson_id == lesson.id,
            VideoProgress.video_asset_id == lesson.video_asset_id,
        )
    )
    if not progress:
        progress = VideoProgress(
            student_id=student.id,
            lesson_id=lesson.id,
            video_asset_id=lesson.video_asset_id,
            last_playback_position=470,
            total_watched_seconds=470,
            completion_percentage=78.33,
        )
        async_session.add(progress)
    else:
        progress.last_playback_position = 470
        progress.total_watched_seconds = 470
        progress.completion_percentage = 78.33
    progress.last_watched_at = datetime.utcnow() - timedelta(minutes=2)
    await async_session.commit()

    response = await async_client.post(
        "/api/v1/videos/progress",
        json={"lesson_id": lesson.id, "video_id": lesson.video_asset_id, "current_position": 480, "duration": 1},
        headers=second_headers,
    )
    assert response.status_code == 200
    assert response.json()["watched_percentage"] >= 80.0

    progress_rows = (
        await async_session.execute(
            select(VideoProgress).where(
                VideoProgress.student_id == student.id,
                VideoProgress.lesson_id == lesson.id,
                VideoProgress.video_asset_id == lesson.video_asset_id,
            )
        )
    ).scalars().all()
    await async_session.refresh(progress_rows[0])
    assert len(progress_rows) == 1
    assert progress_rows[0].is_completed is True

    lesson_progress = await async_session.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == student.id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    await async_session.refresh(lesson_progress)
    assert lesson_progress.video_completed is True


@pytest.mark.asyncio
async def test_video_provider_fails_closed_in_production(async_client: AsyncClient):
    original_environment = settings.ENVIRONMENT
    original_mock = settings.USE_MOCK_VIDEO_PROVIDER
    try:
        login_res = await async_client.post(
            "/api/v1/auth/login",
            json={"identifier": "01011111111", "password": "StudentPass123!@#"},
        )
        assert login_res.status_code == 200
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
        lesson = (await async_client.get("/api/v1/lessons/variables-and-data-types", headers=headers)).json()

        settings.ENVIRONMENT = "production"
        settings.USE_MOCK_VIDEO_PROVIDER = False
        token_response = await async_client.get(
            f"/api/v1/videos/token/{lesson['video_asset_id']}",
            params={"lesson_id": lesson["id"]},
            headers=headers,
        )
        assert token_response.status_code == 503
    finally:
        settings.ENVIRONMENT = original_environment
        settings.USE_MOCK_VIDEO_PROVIDER = original_mock
