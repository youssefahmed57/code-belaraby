from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models import Course, Module, Lesson, User
from app.api.deps import get_current_user
from app.schemas.all_schemas import CourseResponse, ModuleResponse, LessonResponse

import time
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/courses", tags=["Courses"])

_catalog_cache = {}
_course_cache = {}
CACHE_TTL = 15.0 # seconds

@router.get("", response_model=List[CourseResponse])
async def list_courses(
    grade_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    now = time.time()
    cache_key = grade_level or "all"
    if cache_key in _catalog_cache:
        cached_ts, cached_data = _catalog_cache[cache_key]
        if now - cached_ts < CACHE_TTL:
            return cached_data

    stmt = select(Course).where(Course.status == "published", Course.visibility == "public")
    if grade_level:
        stmt = stmt.where(Course.grade_level == grade_level)
    stmt = stmt.order_by(Course.created_at.desc())

    res = await db.execute(stmt)
    courses = res.scalars().all()
    result = [CourseResponse.model_validate(c) for c in courses]
    _catalog_cache[cache_key] = (now, result)
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
    now = time.time()
    if slug in _course_cache:
        cached_ts, cached_data = _course_cache[slug]
        if now - cached_ts < CACHE_TTL:
            return cached_data

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
    _course_cache[slug] = (now, course_dict)
    return course_dict
