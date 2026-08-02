from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.db.models import User
from app.api.deps import get_current_user
from app.schemas.all_schemas import StartQuizResponse, SubmitQuizRequest, QuizAttemptResultResponse
from app.services.quiz_service import start_quiz_attempt, submit_quiz_attempt

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])

@router.post("/{id}/start", response_model=StartQuizResponse)
async def start_quiz(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    attempt = await start_quiz_attempt(db, quiz_id=id, student_id=current_user.id)
    return StartQuizResponse(
        attempt_id=attempt.id,
        quiz_id=attempt.quiz_id,
        time_limit_minutes=15,
        allowed_attempts=3,
        questions=attempt.questions_snapshot
    )

@router.post("/attempts/submit", response_model=QuizAttemptResultResponse)
async def submit_quiz(
    req: SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    attempt = await submit_quiz_attempt(
        db=db,
        attempt_id=req.attempt_id,
        student_id=current_user.id,
        answers=req.answers
    )
    return QuizAttemptResultResponse(
        attempt_id=attempt.id,
        score=attempt.score,
        percentage=attempt.percentage,
        passed=attempt.passed,
        status=attempt.status,
        submitted_at=attempt.submitted_at
    )
