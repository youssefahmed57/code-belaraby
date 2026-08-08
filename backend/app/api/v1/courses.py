from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models import Course, Module, Lesson, User
from app.api.deps import get_current_user
from app.schemas.all_schemas import CourseResponse, ModuleResponse, LessonResponse

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.get("", response_model=List[CourseResponse])
async def list_courses(
    grade_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Course).where(Course.status == "published", Course.visibility == "public")
    if grade_level:
        stmt = stmt.where(Course.grade_level == grade_level)
    stmt = stmt.order_by(Course.created_at.desc())

    res = await db.execute(stmt)
    courses = res.scalars().all()
    return [CourseResponse.model_validate(c) for c in courses]

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
    stmt = select(Course).where(Course.slug == slug, Course.status == "published")
    res = await db.execute(stmt)
    course = res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="الكورس غير موجود.")

    # Fetch modules and lessons hierarchy
    stmt_mods = select(Module).where(Module.course_id == course.id, Module.status == "published").order_by(Module.order)
    res_mods = await db.execute(stmt_mods)
    modules = res_mods.scalars().all()

    modules_data = []
    for mod in modules:
        stmt_l = select(Lesson).where(Lesson.module_id == mod.id, Lesson.publishing_status == "published").order_by(Lesson.order)
        res_l = await db.execute(stmt_l)
        lessons = res_l.scalars().all()

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
                } for l in lessons
            ]
        })

    course_dict = CourseResponse.model_validate(course).model_dump()
    course_dict["modules"] = modules_data
    return course_dict
