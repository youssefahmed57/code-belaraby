from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.db.models import CodingProblem, LessonProgress, Quiz, User
from app.services.access_service import require_accessible_lesson
from app.services.unlock_service import evaluate_lesson_completion


router = APIRouter(prefix="/lessons", tags=["Lessons"])


@router.get("/{id}")
async def get_lesson_details(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lesson = await require_accessible_lesson(db, current_user.id, id)

    lesson_progress = await db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    if not lesson_progress:
        lesson_progress = LessonProgress(student_id=current_user.id, lesson_id=lesson.id, status="in_progress")
        db.add(lesson_progress)
        await db.commit()
        await db.refresh(lesson_progress)

    quiz = await db.scalar(select(Quiz).where(Quiz.lesson_id == lesson.id))
    problem = await db.scalar(select(CodingProblem).where(CodingProblem.lesson_id == lesson.id))

    return {
        "id": lesson.id,
        "title": lesson.title,
        "slug": lesson.slug,
        "description": lesson.description,
        "learning_objectives": lesson.learning_objectives,
        "rich_content": lesson.rich_content,
        "video_asset_id": lesson.video_asset_id,
        "required_video_percentage": lesson.required_video_percentage,
        "passing_score": lesson.passing_score,
        "progress": {
            "status": lesson_progress.status,
            "theory_completed": lesson_progress.theory_completed,
            "video_watched_percentage": lesson_progress.video_watched_percentage,
            "practical_submitted": lesson_progress.practical_submitted,
            "practical_passed": lesson_progress.practical_passed,
            "quiz_passed": lesson_progress.quiz_passed,
            "best_quiz_score": lesson_progress.best_quiz_score,
        },
        "quiz": (
            {
                "id": quiz.id,
                "title": quiz.title,
                "time_limit_minutes": quiz.time_limit_minutes,
                "passing_score": quiz.passing_score,
                "allowed_attempts": quiz.allowed_attempts,
                "availability_start": quiz.availability_start.isoformat() if quiz.availability_start else None,
                "availability_end": quiz.availability_end.isoformat() if quiz.availability_end else None,
            }
            if quiz
            else None
        ),
        "coding_problem": (
            {
                "id": problem.id,
                "title": problem.title,
                "arabic_statement": problem.arabic_statement,
                "difficulty": problem.difficulty,
                "starter_code": problem.starter_code,
                "input_format": problem.input_format,
                "output_format": problem.output_format,
                "supported_languages": problem.supported_languages,
                "time_limit_seconds": problem.time_limit_seconds,
                "memory_limit_mb": problem.memory_limit_mb,
            }
            if problem and problem.status == "published"
            else None
        ),
    }


@router.post("/{id}/complete-theory")
async def mark_theory_completed(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lesson = await require_accessible_lesson(db, current_user.id, id)

    lesson_progress = await db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    if not lesson_progress:
        lesson_progress = LessonProgress(student_id=current_user.id, lesson_id=lesson.id, status="in_progress")
        db.add(lesson_progress)

    lesson_progress.theory_completed = True
    await db.commit()

    lesson_completed, _ = await evaluate_lesson_completion(db, current_user.id, lesson.id)
    return {
        "message": "تم تعليم الجزء النظري كمكتمل بنجاح.",
        "lesson_completed": lesson_completed,
    }
