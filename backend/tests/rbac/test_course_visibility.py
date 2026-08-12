from datetime import datetime, timedelta
import uuid

import pytest
from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.models import Course, Enrolment, Role, User, UserRole


async def _create_private_course(async_session):
    course = Course(
        title=f"Private Course {uuid.uuid4().hex[:6]}",
        slug=f"private-course-{uuid.uuid4().hex[:8]}",
        short_description="Private course",
        full_description="Private course for visibility tests",
        grade_level="first_secondary",
        price=150,
        discount_price=120,
        status="published",
        visibility="private",
        unlock_mode="sequential",
    )
    async_session.add(course)
    await async_session.commit()
    await async_session.refresh(course)
    return course


@pytest.mark.asyncio
async def test_public_course_detail_allows_anonymous_access(async_client):
    response = await async_client.get("/api/v1/courses/python-first-secondary")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_private_course_detail_denies_anonymous_and_random_student(async_client, async_session):
    private_course = await _create_private_course(async_session)

    anonymous_response = await async_client.get(f"/api/v1/courses/{private_course.slug}")
    assert anonymous_response.status_code == 404

    random_student = User(
        arabic_name="طالب بدون اشتراك",
        phone_number=f"010{uuid.uuid4().int % 100000000:08d}",
        email=f"private-{uuid.uuid4().hex[:8]}@codebelaraby.test",
        hashed_password=get_password_hash("Password123"),
        grade_level="first_secondary",
        status="active",
    )
    async_session.add(random_student)
    student_role = await async_session.scalar(select(Role).where(Role.name == "student"))
    await async_session.flush()
    async_session.add(UserRole(user_id=random_student.id, role_id=student_role.id))
    await async_session.commit()

    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": random_student.phone_number, "password": "Password123"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    unauthorized_response = await async_client.get(f"/api/v1/courses/{private_course.slug}", headers=headers)
    assert unauthorized_response.status_code == 404


@pytest.mark.asyncio
async def test_private_course_detail_allows_enrolled_student_and_admin(async_client, async_session):
    private_course = await _create_private_course(async_session)
    student = await async_session.scalar(select(User).where(User.phone_number == "01011111111"))
    assert student is not None

    async_session.add(
        Enrolment(
            student_id=student.id,
            course_id=private_course.id,
            status="active",
            access_start=datetime.utcnow() - timedelta(days=1),
            access_expiry=datetime.utcnow() + timedelta(days=30),
            source="admin_assignment",
        )
    )
    await async_session.commit()

    student_login = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01011111111", "password": "StudentPass123!@#"},
    )
    student_headers = {"Authorization": f"Bearer {student_login.json()['access_token']}"}
    student_response = await async_client.get(f"/api/v1/courses/{private_course.slug}", headers=student_headers)
    assert student_response.status_code == 200
    assert student_response.json()["discount_price"] == 120.0

    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"identifier": "01001340533", "password": "AdminPass123!@#"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    admin_response = await async_client.get(f"/api/v1/courses/{private_course.slug}", headers=admin_headers)
    assert admin_response.status_code == 200
