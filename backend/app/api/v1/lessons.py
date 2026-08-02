from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.db.models import Lesson, Module, Course, User, LessonProgress, Quiz, CodingProblem
from app.api.deps import get_current_user
from app.services.access_service import check_lesson_access
from app.services.unlock_service import evaluate_lesson_completion

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.get("/{id}")
async def get_lesson_details(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Lesson).where(or_(Lesson.id == id, Lesson.slug == id))
    res = await db.execute(stmt)
    lesson = res.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="الدرس غير موجود.")

    # Check access using actual lesson.id
    has_access = await check_lesson_access(db, current_user.id, lesson.id)
    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="هذا الدرس مغلق. يجب إكمال الدروس السابقة أو تفعيل الاشتراك كأولى خطوة."
        )

    # Fetch progress
    stmt_lp = select(LessonProgress).where(
        LessonProgress.student_id == current_user.id,
        LessonProgress.lesson_id == lesson.id
    )
    res_lp = await db.execute(stmt_lp)
    lp = res_lp.scalar_one_or_none()

    if not lp:
        lp = LessonProgress(student_id=current_user.id, lesson_id=lesson.id, status="in_progress")
        db.add(lp)
        await db.commit()
        await db.refresh(lp)

    # Fetch attached quiz if exists
    stmt_quiz = select(Quiz).where(Quiz.lesson_id == lesson.id)
    res_quiz = await db.execute(stmt_quiz)
    quiz = res_quiz.scalar_one_or_none()

    # Fetch attached coding problem if exists
    stmt_prob = select(CodingProblem).where(CodingProblem.lesson_id == lesson.id)
    res_prob = await db.execute(stmt_prob)
    prob = res_prob.scalar_one_or_none()

    return {
        "id": lesson.id,
        "title": lesson.title,
        "slug": lesson.slug,
        "description": lesson.description,
        "learning_objectives": lesson.learning_objectives,
        "rich_content": lesson.rich_content,
        "video_asset_id": lesson.video_asset_id,
        "passing_score": lesson.passing_score,
        "progress": {
            "status": lp.status,
            "theory_completed": lp.theory_completed,
            "video_watched_percentage": lp.video_watched_percentage,
            "practical_submitted": lp.practical_submitted,
            "practical_passed": lp.practical_passed,
            "quiz_passed": lp.quiz_passed,
            "best_quiz_score": lp.best_quiz_score
        },
        "quiz": {
            "id": quiz.id,
            "title": quiz.title,
            "time_limit_minutes": quiz.time_limit_minutes,
            "passing_score": quiz.passing_score,
            "allowed_attempts": quiz.allowed_attempts
        } if quiz else None,
        "coding_problem": {
            "id": prob.id,
            "title": prob.title,
            "arabic_statement": prob.arabic_statement,
            "difficulty": prob.difficulty,
            "starter_code": prob.starter_code,
            "input_format": prob.input_format,
            "output_format": prob.output_format
        } if prob else None
    }

@router.post("/{id}/complete-theory")
async def mark_theory_completed(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_lesson = select(Lesson).where(or_(Lesson.id == id, Lesson.slug == id))
    res_l = await db.execute(stmt_lesson)
    lesson = res_l.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="الدرس غير موجود.")

    stmt_lp = select(LessonProgress).where(
        LessonProgress.student_id == current_user.id,
        LessonProgress.lesson_id == lesson.id
    )
    res_lp = await db.execute(stmt_lp)
    lp = res_lp.scalar_one_or_none()
    if not lp:
        lp = LessonProgress(student_id=current_user.id, lesson_id=lesson.id, status="in_progress")
        db.add(lp)

    lp.theory_completed = True
    await db.commit()

    is_completed, updated_lp = await evaluate_lesson_completion(db, current_user.id, lesson.id)
    return {"message": "تم تعليم الجزء النظري كمكتمل بنجاح.", "lesson_completed": is_completed}
