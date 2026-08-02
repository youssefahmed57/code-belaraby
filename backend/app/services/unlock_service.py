from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.models import (
    LessonProgress, Lesson, Module, Course, AuditLog, Notification,
    VideoProgress, CodeSubmission, QuizAttempt
)

async def evaluate_lesson_completion(db: AsyncSession, student_id: str, lesson_id: str) -> Tuple[bool, LessonProgress]:
    stmt_lesson = select(Lesson).where(Lesson.id == lesson_id)
    res_l = await db.execute(stmt_lesson)
    lesson = res_l.scalar_one_or_none()

    stmt_lp = select(LessonProgress).where(
        LessonProgress.student_id == student_id,
        LessonProgress.lesson_id == lesson_id
    )
    res_lp = await db.execute(stmt_lp)
    lp = res_lp.scalar_one_or_none()

    if not lp:
        lp = LessonProgress(student_id=student_id, lesson_id=lesson_id, status="in_progress")
        db.add(lp)
        await db.flush()

    if lp.manual_override:
        lp.status = "completed"
        if not lp.completed_at:
            lp.completed_at = datetime.utcnow()
        await db.commit()
        if lesson:
            await unlock_next_lesson(db, student_id, lesson)
        return True, lp

    req_video_pct = lesson.required_video_percentage if lesson else 80.0
    req_practical = lesson.required_practical_submission if lesson else True
    req_quiz = lesson.required_quiz_pass if lesson else True
    passing_score = lesson.passing_score if lesson else 70.0

    video_ok = lp.video_watched_percentage >= req_video_pct if req_video_pct > 0 else True
    theory_ok = lp.theory_completed
    practical_ok = lp.practical_passed if req_practical else True
    quiz_ok = (lp.best_quiz_score >= passing_score) if req_quiz else True

    is_completed = video_ok and theory_ok and practical_ok and quiz_ok

    if is_completed:
        lp.status = "completed"
        if not lp.completed_at:
            lp.completed_at = datetime.utcnow()
        await db.commit()
        if lesson:
            await unlock_next_lesson(db, student_id, lesson)
    else:
        lp.status = "in_progress"
        await db.commit()

    return is_completed, lp

async def unlock_next_lesson(db: AsyncSession, student_id: str, current_lesson: Lesson):
    # Fetch module course_id safely
    stmt_mod_c = select(Module.course_id).where(Module.id == current_lesson.module_id)
    res_mod_c = await db.execute(stmt_mod_c)
    course_id = res_mod_c.scalar_one_or_none()

    # Find next lesson in same module or first lesson in next module
    stmt_next = select(Lesson).where(
        Lesson.module_id == current_lesson.module_id,
        Lesson.order > current_lesson.order,
        Lesson.publishing_status == "published"
    ).order_by(Lesson.order)
    res_next = await db.execute(stmt_next)
    next_lesson = res_next.scalars().first()

    if not next_lesson and course_id:
        stmt_mod = select(Module).where(
            Module.course_id == course_id,
            Module.order > 1,
            Module.status == "published"
        ).order_by(Module.order)
        res_mod = await db.execute(stmt_mod)
        next_mod = res_mod.scalars().first()

        if next_mod:
            stmt_m1_l1 = select(Lesson).where(
                Lesson.module_id == next_mod.id,
                Lesson.publishing_status == "published"
            ).order_by(Lesson.order)
            res_m1 = await db.execute(stmt_m1_l1)
            next_lesson = res_m1.scalars().first()

    if next_lesson:
        stmt_lp = select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == next_lesson.id
        )
        res_lp = await db.execute(stmt_lp)
        lp = res_lp.scalar_one_or_none()
        if not lp:
            db.add(LessonProgress(
                student_id=student_id,
                lesson_id=next_lesson.id,
                status="available"
            ))
        elif lp.status == "locked":
            lp.status = "available"
        await db.commit()

async def admin_manual_lesson_unlock(
    db: AsyncSession,
    student_id: str,
    lesson_id: str,
    admin_id: str,
    reason: str,
    action: str = "unlock"
) -> LessonProgress:
    stmt_lp = select(LessonProgress).where(
        LessonProgress.student_id == student_id,
        LessonProgress.lesson_id == lesson_id
    )
    res_lp = await db.execute(stmt_lp)
    lp = res_lp.scalar_one_or_none()

    if not lp:
        lp = LessonProgress(student_id=student_id, lesson_id=lesson_id)
        db.add(lp)

    if action == "unlock":
        lp.status = "completed"
        lp.manual_override = True
        lp.manual_override_by_id = admin_id
        lp.override_reason = reason
        lp.completed_at = datetime.utcnow()
    elif action == "lock":
        lp.status = "locked"
        lp.manual_override = False
        lp.override_reason = reason
    elif action == "reset":
        lp.status = "available"
        lp.theory_completed = False
        lp.video_watched_percentage = 0.0
        lp.video_completed = False
        lp.practical_submitted = False
        lp.practical_passed = False
        lp.quiz_passed = False
        lp.best_quiz_score = 0.0
        lp.manual_override = False
        lp.override_reason = reason

    db.add(AuditLog(
        user_id=admin_id,
        action=f"MANUAL_LESSON_{action.upper()}",
        entity_type="lesson_progress",
        entity_id=lp.id,
        details={"student_id": student_id, "lesson_id": lesson_id, "reason": reason}
    ))

    await db.commit()
    await db.refresh(lp)
    return lp
