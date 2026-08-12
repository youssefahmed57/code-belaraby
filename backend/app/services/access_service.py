from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    CodingProblem,
    Enrolment,
    Lesson,
    LessonPrerequisite,
    LessonProgress,
    Module,
    Quiz,
    User,
    VideoAsset,
    Course,
)


async def check_course_access(
    db: AsyncSession,
    student_id: str,
    course_id: str,
) -> Tuple[bool, Optional[Enrolment]]:
    student = await db.scalar(select(User).where(User.id == student_id))
    if not student or student.status != "active":
        return False, None

    course = await db.scalar(select(Course).where(Course.id == course_id))
    if not course or course.status != "published":
        return False, None

    enrolment = await db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == student_id,
            Enrolment.course_id == course_id,
            Enrolment.status == "active",
        )
    )
    if not enrolment:
        return False, None

    now = datetime.utcnow()
    if enrolment.access_start and enrolment.access_start > now:
        return False, enrolment
    if enrolment.access_expiry and enrolment.access_expiry < now:
        return False, enrolment
    return True, enrolment


async def get_lesson_by_reference(db: AsyncSession, lesson_ref: str) -> Optional[Lesson]:
    result = await db.execute(
        select(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
        .where(or_(Lesson.id == lesson_ref, Lesson.slug == lesson_ref))
    )
    return result.scalar_one_or_none()


async def check_lesson_access(db: AsyncSession, student_id: str, lesson_id: str) -> bool:
    row = (
        await db.execute(
            select(Lesson, Module, Course)
            .join(Module, Lesson.module_id == Module.id)
            .join(Course, Module.course_id == Course.id)
            .where(or_(Lesson.id == lesson_id, Lesson.slug == lesson_id))
        )
    ).first()
    if not row:
        return False

    lesson, module, course = row
    if lesson.publishing_status != "published" or module.status != "published" or course.status != "published":
        return False

    has_course_access, _ = await check_course_access(db, student_id, course.id)
    if not has_course_access:
        return False

    progress = await db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    if progress and (progress.manual_override or progress.status in {"available", "in_progress", "completed"}):
        return True

    prereq_ids = (
        await db.execute(
            select(LessonPrerequisite.prerequisite_lesson_id).where(LessonPrerequisite.lesson_id == lesson.id)
        )
    ).scalars().all()

    if not prereq_ids:
        return lesson.order == 1

    for prereq_id in prereq_ids:
        prereq_progress = await db.scalar(
            select(LessonProgress).where(
                LessonProgress.student_id == student_id,
                LessonProgress.lesson_id == prereq_id,
            )
        )
        if not prereq_progress or prereq_progress.status != "completed":
            return False
    return True


async def require_accessible_lesson(db: AsyncSession, student_id: str, lesson_ref: str) -> Lesson:
    lesson = await get_lesson_by_reference(db, lesson_ref)
    if not lesson:
        raise HTTPException(status_code=404, detail="الدرس غير موجود.")
    if not await check_lesson_access(db, student_id, lesson.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذا الدرس مغلق أو غير متاح لحسابك حالياً.",
        )
    return lesson


async def require_accessible_problem(
    db: AsyncSession,
    student_id: str,
    problem_id: str,
    requested_language: str,
) -> tuple[CodingProblem, Lesson]:
    problem = await db.scalar(select(CodingProblem).where(CodingProblem.id == problem_id))
    if not problem:
        raise HTTPException(status_code=404, detail="المسألة غير موجودة.")
    if problem.status != "published":
        raise HTTPException(status_code=404, detail="المسألة غير منشورة.")
    if not problem.lesson_id:
        raise HTTPException(status_code=400, detail="المسألة غير مرتبطة بدرس منشور.")
    if requested_language.lower() not in {lang.lower() for lang in (problem.supported_languages or [])}:
        raise HTTPException(status_code=400, detail="لغة الحل المطلوبة غير مدعومة لهذه المسألة.")

    lesson = await require_accessible_lesson(db, student_id, problem.lesson_id)
    return problem, lesson


async def require_accessible_quiz(db: AsyncSession, student_id: str, quiz_id: str) -> tuple[Quiz, Optional[Lesson]]:
    quiz = await db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise HTTPException(status_code=404, detail="الاختبار غير موجود.")

    lesson = None
    if quiz.lesson_id:
        lesson = await require_accessible_lesson(db, student_id, quiz.lesson_id)
    return quiz, lesson


async def require_accessible_video(
    db: AsyncSession,
    student_id: str,
    lesson_id: str,
    video_id: str,
) -> tuple[Lesson, VideoAsset]:
    lesson = await require_accessible_lesson(db, student_id, lesson_id)
    if lesson.video_asset_id != video_id:
        raise HTTPException(status_code=403, detail="الفيديو لا ينتمي إلى هذا الدرس.")

    video_asset = await db.scalar(select(VideoAsset).where(VideoAsset.id == video_id))
    if not video_asset:
        raise HTTPException(status_code=404, detail="الفيديو غير موجود.")
    return lesson, video_asset
