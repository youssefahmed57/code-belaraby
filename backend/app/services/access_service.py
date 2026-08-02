from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status

from app.db.models import User, Course, Lesson, Module, Enrolment, LessonProgress, LessonPrerequisite

async def check_course_access(db: AsyncSession, student_id: str, course_id: str) -> Tuple[bool, Optional[Enrolment]]:
    stmt_user = select(User).where(User.id == student_id)
    res_user = await db.execute(stmt_user)
    student = res_user.scalar_one_or_none()
    if not student or student.status != "active":
        return False, None

    stmt_enrol = select(Enrolment).where(
        Enrolment.student_id == student_id,
        Enrolment.course_id == course_id,
        Enrolment.status == "active"
    )
    res_enrol = await db.execute(stmt_enrol)
    enrolment = res_enrol.scalar_one_or_none()

    if not enrolment:
        return False, None

    now = datetime.utcnow()
    if enrolment.access_expiry and enrolment.access_expiry < now:
        return False, enrolment

    return True, enrolment

async def check_lesson_access(db: AsyncSession, student_id: str, lesson_id: str) -> bool:
    # Explicitly join Lesson and Module to fetch course_id without lazy relationship loading
    stmt_lesson = select(Lesson, Module.course_id).join(Module, Lesson.module_id == Module.id).where(
        or_(Lesson.id == lesson_id, Lesson.slug == lesson_id)
    )
    res_lesson = await db.execute(stmt_lesson)
    row = res_lesson.first()
    if not row:
        return False

    lesson, course_id = row
    if lesson.publishing_status != "published":
        return False

    # Check course access
    has_course_access, _ = await check_course_access(db, student_id, course_id)
    if not has_course_access:
        return False

    # Check manual override or explicit progress status
    stmt_lp = select(LessonProgress).where(
        LessonProgress.student_id == student_id,
        LessonProgress.lesson_id == lesson.id
    )
    res_lp = await db.execute(stmt_lp)
    lp = res_lp.scalar_one_or_none()

    if lp and (lp.manual_override or lp.status in ["available", "in_progress", "completed"]):
        return True

    # Check prerequisites
    stmt_prereq = select(LessonPrerequisite.prerequisite_lesson_id).where(LessonPrerequisite.lesson_id == lesson.id)
    res_prereq = await db.execute(stmt_prereq)
    prereq_ids = res_prereq.scalars().all()

    if not prereq_ids:
        if lesson.order == 1:
            return True

    for prereq_id in prereq_ids:
        stmt_p_lp = select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == prereq_id
        )
        res_p_lp = await db.execute(stmt_p_lp)
        p_lp = res_p_lp.scalar_one_or_none()
        if not p_lp or p_lp.status != "completed":
            return False

    return True
