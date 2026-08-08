from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models import Course, Module, Lesson, User
from app.api.deps import get_current_user
from app.schemas.all_schemas import CourseResponse, ModuleResponse, LessonResponse

from sqlalchemy.orm import selectinload
from app.core.cache import cache_get, cache_set, cache_invalidate

router = APIRouter(prefix="/courses", tags=["Courses"])

CATALOG_CACHE_TTL = 300 # 5 minutes per user recommendation

@router.get("", response_model=List[CourseResponse])
async def list_courses(
    grade_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"catalog:{grade_level or 'all'}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    stmt = select(Course).where(Course.status == "published", Course.visibility == "public")
    if grade_level:
        stmt = stmt.where(Course.grade_level == grade_level)
    stmt = stmt.order_by(Course.created_at.desc())

    res = await db.execute(stmt)
    courses = res.scalars().all()
    result = [CourseResponse.model_validate(c).model_dump() for c in courses]
    cache_set(cache_key, result, ttl_seconds=CATALOG_CACHE_TTL)
    return result

@router.get("/my-enrolments", response_model=List[CourseResponse])
@router.get("/my-courses", response_model=List[CourseResponse])
async def list_my_enrolled_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.db.models import Enrolment
    stmt = (
        select(Course)
        .join(Enrolment, Enrolment.course_id == Course.id)
        .where(
            Enrolment.student_id == current_user.id,
            Enrolment.status == "active",
            Course.status == "published"
        )
        .order_by(Course.created_at.desc())
    )
    res = await db.execute(stmt)
    courses = res.scalars().all()
    return [CourseResponse.model_validate(c) for c in courses]

@router.get("/{slug}")
async def get_course_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    cache_key = f"course_slug:{slug}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    stmt = (
        select(Course)
        .options(selectinload(Course.modules).selectinload(Module.lessons))
        .where(Course.slug == slug, Course.status == "published")
    )
    res = await db.execute(stmt)
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="الكورس غير موجود.")

    modules_data = []
    sorted_modules = sorted([m for m in course.modules if m.status == "published"], key=lambda m: m.order)
    for mod in sorted_modules:
        sorted_lessons = sorted([l for l in mod.lessons if l.publishing_status == "published"], key=lambda l: l.order)
        modules_data.append({
            "id": mod.id,
            "title": mod.title,
            "description": mod.description,
            "order": mod.order,
            "lessons": [
                {
                    "id": l.id,
                    "title": l.title,
                    "slug": l.slug,
                    "duration": l.estimated_duration_minutes,
                    "is_preview": l.preview_status,
                    "order": l.order
                } for l in sorted_lessons
            ]
        })

    course_dict = CourseResponse.model_validate(course).model_dump()
    course_dict["modules"] = modules_data
    cache_set(cache_key, course_dict, ttl_seconds=CATALOG_CACHE_TTL)
    return course_dict
