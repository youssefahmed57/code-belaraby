import random
from datetime import datetime
from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    LessonProgress,
    Question,
    QuestionOption,
    Quiz,
    QuizAttempt,
    QuizAttemptQuestion,
    QuizQuestion,
    StudentAnswer,
)


async def start_quiz_attempt(db: AsyncSession, quiz_id: str, student_id: str) -> QuizAttempt:
    quiz = await db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise HTTPException(status_code=404, detail="الاختبار غير موجود.")

    now = datetime.utcnow()
    if quiz.availability_start and now < quiz.availability_start:
        raise HTTPException(status_code=403, detail="الاختبار غير متاح بعد.")
    if quiz.availability_end and now > quiz.availability_end:
        raise HTTPException(status_code=403, detail="انتهت نافذة إتاحة هذا الاختبار.")

    existing_attempts = (
        await db.execute(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
            )
        )
    ).scalars().all()

    if quiz.allowed_attempts > 0 and len(existing_attempts) >= quiz.allowed_attempts:
        raise HTTPException(
            status_code=400,
            detail=f"لقد استنفدت عدد المحاولات المتاحة لهذا الاختبار ({quiz.allowed_attempts} محاولات).",
        )

    quiz_rows = (
        await db.execute(
            select(QuizQuestion, Question)
            .join(Question, QuizQuestion.question_id == Question.id)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.order)
        )
    ).all()
    if not quiz_rows:
        raise HTTPException(status_code=400, detail="الاختبار لا يحتوي على أسئلة حالياً.")

    question_snapshots = []
    for quiz_question, question in quiz_rows:
        options = (
            await db.execute(
                select(QuestionOption).where(QuestionOption.question_id == question.id).order_by(QuestionOption.order)
            )
        ).scalars().all()
        option_data = [{"id": option.id, "text": option.option_text, "order": option.order} for option in options]
        if quiz.shuffle_options:
            random.shuffle(option_data)
        question_snapshots.append(
            {
                "id": question.id,
                "title": question.title,
                "text": question.question_text,
                "type": question.question_type,
                "points": quiz_question.points_override if quiz_question.points_override is not None else question.points,
                "options": option_data,
                "image_url": question.image_url,
            }
        )

    if quiz.shuffle_questions:
        random.shuffle(question_snapshots)

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=student_id,
        attempt_number=len(existing_attempts) + 1,
        status="in_progress",
        start_time=now,
        questions_snapshot=question_snapshots,
    )
    db.add(attempt)
    await db.flush()

    for snapshot in question_snapshots:
        db.add(
            QuizAttemptQuestion(
                attempt_id=attempt.id,
                question_id=snapshot["id"],
                question_snapshot=snapshot,
                points_awarded=0.0,
                is_correct=False,
            )
        )

    await db.commit()
    await db.refresh(attempt)
    return attempt


async def submit_quiz_attempt(
    db: AsyncSession,
    attempt_id: str,
    student_id: str,
    answers: List[Dict[str, Any]],
) -> QuizAttempt:
    attempt = await db.scalar(
        select(QuizAttempt).where(QuizAttempt.id == attempt_id, QuizAttempt.student_id == student_id)
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="محاولة الاختبار غير موجودة.")
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="تم تسليم هذه المحاولة من قبل.")

    quiz = await db.scalar(select(Quiz).where(Quiz.id == attempt.quiz_id))
    if not quiz:
        raise HTTPException(status_code=404, detail="الاختبار غير موجود.")

    timed_out = False
    if quiz.time_limit_minutes > 0:
        elapsed_seconds = (datetime.utcnow() - attempt.start_time).total_seconds()
        if elapsed_seconds > quiz.time_limit_minutes * 60:
            timed_out = True

    attempt_questions = (
        await db.execute(select(QuizAttemptQuestion).where(QuizAttemptQuestion.attempt_id == attempt_id))
    ).scalars().all()
    valid_question_ids = {attempt_question.question_id for attempt_question in attempt_questions}

    answers_by_question: dict[str, Dict[str, Any]] = {}
    for answer in answers:
        question_id = answer.get("question_id")
        if not question_id:
            raise HTTPException(status_code=400, detail="إجابة بدون question_id غير صالحة.")
        if question_id in answers_by_question:
            raise HTTPException(status_code=400, detail="تم إرسال السؤال نفسه أكثر من مرة في نفس المحاولة.")
        if question_id not in valid_question_ids:
            raise HTTPException(status_code=400, detail="إحدى الإجابات لا تنتمي إلى هذه المحاولة.")
        answers_by_question[question_id] = answer

    total_possible = 0.0
    total_awarded = 0.0

    for attempt_question in attempt_questions:
        question_snapshot = attempt_question.question_snapshot
        question_id = attempt_question.question_id
        question_points = float(question_snapshot.get("points", 1.0))
        total_possible += question_points

        answer_payload = answers_by_question.get(question_id, {})
        selected_option_ids = answer_payload.get("selected_option_ids") or []
        text_answer = answer_payload.get("text_answer") or ""

        valid_option_ids = {
            option_id
            for option_id, in (
                await db.execute(select(QuestionOption.id).where(QuestionOption.question_id == question_id))
            ).all()
        }
        invalid_option_ids = [option_id for option_id in selected_option_ids if option_id not in valid_option_ids]
        if invalid_option_ids:
            raise HTTPException(status_code=400, detail="تم إرسال خيارات لا تنتمي إلى السؤال.")

        question_type = question_snapshot.get("type")
        if question_type in {"single_mcq", "true_false"} and len(selected_option_ids) > 1:
            raise HTTPException(status_code=400, detail="لا يمكن اختيار أكثر من إجابة لهذا السؤال.")

        db.add(
            StudentAnswer(
                attempt_question_id=attempt_question.id,
                selected_option_ids=selected_option_ids,
                text_answer=text_answer,
            )
        )

        correct_option_ids = {
            option_id
            for option_id, in (
                await db.execute(
                    select(QuestionOption.id).where(
                        QuestionOption.question_id == question_id,
                        QuestionOption.is_correct.is_(True),
                    )
                )
            ).all()
        }

        is_correct = bool(selected_option_ids) and set(selected_option_ids) == correct_option_ids
        attempt_question.is_correct = is_correct
        attempt_question.points_awarded = question_points if is_correct else 0.0
        total_awarded += attempt_question.points_awarded

    attempt.score = round(total_awarded, 2)
    attempt.percentage = round((total_awarded / total_possible * 100.0) if total_possible else 0.0, 2)
    attempt.end_time = datetime.utcnow()
    attempt.submitted_at = attempt.end_time
    attempt.status = "timed_out" if timed_out else "submitted"
    attempt.passed = False if timed_out else attempt.percentage >= quiz.passing_score

    if quiz.lesson_id and not timed_out:
        lesson_progress = await db.scalar(
            select(LessonProgress).where(
                LessonProgress.student_id == student_id,
                LessonProgress.lesson_id == quiz.lesson_id,
            )
        )
        if not lesson_progress:
            lesson_progress = LessonProgress(student_id=student_id, lesson_id=quiz.lesson_id, status="in_progress")
            db.add(lesson_progress)
        lesson_progress.best_quiz_score = max(lesson_progress.best_quiz_score or 0.0, attempt.percentage)
        if attempt.passed:
            lesson_progress.quiz_passed = True

    await db.commit()
    await db.refresh(attempt)
    return attempt
