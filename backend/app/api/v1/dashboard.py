from datetime import datetime, timedelta, date
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.db.models import (
    User, Course, Module, Lesson, Enrolment, LessonProgress,
    QuizAttempt, CodeSubmission
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()

    # 1. Fetch active enrolments for current student where course is published
    stmt_enrols = (
        select(Enrolment, Course)
        .join(Course, Enrolment.course_id == Course.id)
        .where(
            Enrolment.student_id == current_user.id,
            Enrolment.status == "active",
            Course.status == "published"
        )
    )
    res_enrols = await db.execute(stmt_enrols)
    enrolments_courses = res_enrols.all()

    active_courses = []
    enrolled_course_ids = set()

    for enrol, course in enrolments_courses:
        # Filter out expired or unstarted enrolments
        if enrol.access_expiry and enrol.access_expiry < now:
            continue
        if enrol.access_start and enrol.access_start > now:
            continue

        enrolled_course_ids.add(course.id)

        # Get published modules for this course
        stmt_mods = select(Module.id).where(
            Module.course_id == course.id,
            Module.status == "published"
        )
        res_mods = await db.execute(stmt_mods)
        mod_ids = res_mods.scalars().all()

        total_course_lessons = 0
        completed_lessons_count = 0
        next_lesson_slug = "variables-and-data-types"

        if mod_ids:
            # Fetch published lessons
            stmt_lessons = (
                select(Lesson)
                .where(
                    Lesson.module_id.in_(mod_ids),
                    Lesson.publishing_status == "published"
                )
                .order_by(Lesson.order)
            )
            res_lessons = await db.execute(stmt_lessons)
            lessons = res_lessons.scalars().all()
            total_course_lessons = len(lessons)

            if lessons:
                next_lesson_slug = lessons[0].slug
                lesson_ids = [l.id for l in lessons]

                # Fetch lesson progress for these lessons
                stmt_lp = select(LessonProgress).where(
                    LessonProgress.student_id == current_user.id,
                    LessonProgress.lesson_id.in_(lesson_ids)
                )
                res_lp = await db.execute(stmt_lp)
                progresses = res_lp.scalars().all()
                completed_ids = set()

                for lp in progresses:
                    is_done = (
                        lp.status == "completed" or
                        (lp.theory_completed and lp.quiz_passed and lp.practical_submitted)
                    )
                    if is_done:
                        completed_ids.add(lp.lesson_id)

                completed_lessons_count = len(completed_ids)

                # Find first uncompleted lesson for next_lesson_slug
                for l in lessons:
                    if l.id not in completed_ids:
                        next_lesson_slug = l.slug
                        break

        progress_percentage = (
            round((completed_lessons_count / total_course_lessons) * 100, 1)
            if total_course_lessons > 0 else 0.0
        )

        access_expiry_str = (
            enrol.access_expiry.strftime("%Y-%m-%d")
            if enrol.access_expiry else None
        )

        active_courses.append({
            "id": course.id,
            "title": course.title,
            "slug": course.slug,
            "short_description": course.short_description,
            "grade_level": course.grade_level,
            "price": course.price,
            "discount_price": course.discount_price,
            "access_expiry": access_expiry_str,
            "access_duration_days": course.access_duration_days,
            "progress_percentage": progress_percentage,
            "completed_lessons": completed_lessons_count,
            "total_lessons": total_course_lessons,
            "next_lesson_slug": next_lesson_slug,
            "status": "active",
            "is_enrolled": True
        })

    # 2. Fetch suggested / promotional published courses student is NOT enrolled in
    stmt_suggested = select(Course).where(
        Course.status == "published",
        Course.visibility == "public"
    )
    if enrolled_course_ids:
        stmt_suggested = stmt_suggested.where(Course.id.not_in(enrolled_course_ids))

    res_suggested = await db.execute(stmt_suggested)
    suggested_raw = res_suggested.scalars().all()

    suggested_courses = [
        {
            "id": c.id,
            "title": c.title,
            "slug": c.slug,
            "short_description": c.short_description,
            "grade_level": c.grade_level,
            "price": c.price,
            "discount_price": c.discount_price,
            "is_enrolled": False
        }
        for c in suggested_raw
    ]

    # 3. Calculate summary metrics
    completed_lessons_total = sum(c["completed_lessons"] for c in active_courses)
    total_lessons_total = sum(c["total_lessons"] for c in active_courses)

    # Real Average quiz score
    stmt_quiz = select(func.avg(QuizAttempt.percentage)).where(
        QuizAttempt.student_id == current_user.id,
        QuizAttempt.status == "submitted"
    )
    res_quiz = await db.execute(stmt_quiz)
    avg_score = res_quiz.scalar()
    if avg_score is not None:
        average_quiz_score = round(float(avg_score), 1)
    else:
        average_quiz_score = 0.0

    # Real Learning streak calculation
    res_q_dates = await db.execute(
        select(func.date(QuizAttempt.submitted_at)).where(
            QuizAttempt.student_id == current_user.id,
            QuizAttempt.submitted_at.isnot(None)
        )
    )
    res_lp_dates = await db.execute(
        select(func.date(LessonProgress.updated_at)).where(
            LessonProgress.student_id == current_user.id
        )
    )
    res_sub_dates = await db.execute(
        select(func.date(CodeSubmission.created_at)).where(
            CodeSubmission.student_id == current_user.id
        )
    )

    activity_dates = set()
    for d in (res_q_dates.scalars().all() + res_lp_dates.scalars().all() + res_sub_dates.scalars().all()):
        if d:
            if isinstance(d, str):
                try:
                    d = datetime.strptime(d, "%Y-%m-%d").date()
                except Exception:
                    continue
            elif isinstance(d, datetime):
                d = d.date()
            activity_dates.add(d)

    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    if not activity_dates:
        learning_streak_days = 0
    else:
        curr = today if today in activity_dates else (yesterday if yesterday in activity_dates else None)
        if curr is None:
            learning_streak_days = 0
        else:
            streak = 0
            while curr in activity_dates:
                streak += 1
                curr -= timedelta(days=1)
            learning_streak_days = streak

    return {
        "active_enrolment_count": len(active_courses),
        "completed_lessons": completed_lessons_total,
        "total_lessons": total_lessons_total,
        "average_quiz_score": average_quiz_score,
        "learning_streak_days": learning_streak_days,
        "courses": active_courses,
        "suggested_courses": suggested_courses
    }
