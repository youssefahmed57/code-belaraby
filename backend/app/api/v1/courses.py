from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_optional_current_user, get_user_role_names
from app.core.cache import cache_get, cache_set
from app.core.database import get_db
from app.db.models import Course, Module, User
from app.schemas.all_schemas import CourseResponse
from app.services.access_service import check_course_access


router = APIRouter(prefix="/courses", tags=["Courses"])

CATALOG_CACHE_TTL = 300


@router.get("", response_model=List[CourseResponse])
async def list_courses(
    grade_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"catalog:{grade_level or 'all'}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    statement = select(Course).where(Course.status == "published", Course.visibility == "public")
    if grade_level:
        statement = statement.where(Course.grade_level == grade_level)
    statement = statement.order_by(Course.created_at.desc())

    courses = (await db.execute(statement)).scalars().all()
    response = [CourseResponse.model_validate(course).model_dump() for course in courses]
    cache_set(cache_key, response, ttl_seconds=CATALOG_CACHE_TTL)
    return response


@router.get("/my-enrolments", response_model=List[CourseResponse])
@router.get("/my-courses", response_model=List[CourseResponse])
async def list_my_enrolled_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.db.models import Enrolment

    statement = (
        select(Course)
        .join(Enrolment, Enrolment.course_id == Course.id)
        .where(
            Enrolment.student_id == current_user.id,
            Enrolment.status == "active",
            Course.status == "published",
        )
        .order_by(Course.created_at.desc())
    )
    courses = (await db.execute(statement)).scalars().all()
    return [CourseResponse.model_validate(course) for course in courses]


@router.get("/{slug}")
async def get_course_by_slug(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    statement = (
        select(Course)
        .options(selectinload(Course.modules).selectinload(Module.lessons))
        .where(Course.slug == slug, Course.status == "published")
    )
    course = (await db.execute(statement)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="الكورس غير موجود.")

    if course.visibility != "public":
        if current_user is None:
            raise HTTPException(status_code=404, detail="الكورس غير موجود.")
        role_names = await get_user_role_names(db, current_user.id)
        is_admin = "admin" in role_names or "super_admin" in role_names
        if not is_admin:
            has_access, _ = await check_course_access(db, current_user.id, course.id)
            if not has_access:
                raise HTTPException(status_code=404, detail="الكورس غير موجود.")

    modules_data = []
    published_modules = sorted(
        [module for module in course.modules if module.status == "published"],
        key=lambda module: module.order,
    )
    for module in published_modules:
        published_lessons = sorted(
            [lesson for lesson in module.lessons if lesson.publishing_status == "published"],
            key=lambda lesson: lesson.order,
        )
        modules_data.append(
            {
                "id": module.id,
                "title": module.title,
                "description": module.description,
                "order": module.order,
                "lessons": [
                    {
                        "id": lesson.id,
                        "title": lesson.title,
                        "slug": lesson.slug,
                        "duration": lesson.estimated_duration_minutes,
                        "is_preview": lesson.preview_status,
                        "order": lesson.order,
                    }
                    for lesson in published_lessons
                ],
            }
        )

    course_payload = CourseResponse.model_validate(course).model_dump()
    course_payload["modules"] = modules_data
    return course_payload
