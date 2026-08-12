from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.db.models import Quiz, User
from app.schemas.all_schemas import QuizAttemptResultResponse, StartQuizResponse, SubmitQuizRequest
from app.services.access_service import require_accessible_quiz
from app.services.quiz_service import start_quiz_attempt, submit_quiz_attempt
from app.services.unlock_service import evaluate_lesson_completion


router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("/{id}/start", response_model=StartQuizResponse)
async def start_quiz(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="الحساب غير مفعل.")

    quiz, _lesson = await require_accessible_quiz(db, current_user.id, id)
    attempt = await start_quiz_attempt(db, quiz_id=id, student_id=current_user.id)

    return StartQuizResponse(
        attempt_id=attempt.id,
        quiz_id=attempt.quiz_id,
        time_limit_minutes=quiz.time_limit_minutes,
        allowed_attempts=quiz.allowed_attempts,
        questions=attempt.questions_snapshot or [],
    )


@router.post("/attempts/submit", response_model=QuizAttemptResultResponse)
async def submit_quiz(
    req: SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="الحساب غير مفعل.")

    attempt = await submit_quiz_attempt(
        db=db,
        attempt_id=req.attempt_id,
        student_id=current_user.id,
        answers=req.answers,
    )

    quiz = await db.scalar(select(Quiz).where(Quiz.id == attempt.quiz_id))
    if quiz and quiz.lesson_id and attempt.status != "timed_out":
        await evaluate_lesson_completion(db, current_user.id, quiz.lesson_id)

    total_questions = len(attempt.questions_snapshot or [])
    correct_count = int(round((attempt.percentage / 100.0) * total_questions)) if total_questions else 0
    return QuizAttemptResultResponse(
        attempt_id=attempt.id,
        score=attempt.score,
        percentage=attempt.percentage,
        passed=attempt.passed,
        status=attempt.status,
        submitted_at=attempt.submitted_at,
        correct_count=correct_count,
        total_questions=total_questions,
    )
