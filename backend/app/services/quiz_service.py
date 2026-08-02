import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.db.models import (
    Quiz, Question, QuestionOption, QuizQuestion, QuizAttempt,
    QuizAttemptQuestion, StudentAnswer, LessonProgress
)

async def start_quiz_attempt(db: AsyncSession, quiz_id: str, student_id: str) -> QuizAttempt:
    stmt_quiz = select(Quiz).where(Quiz.id == quiz_id)
    res_quiz = await db.execute(stmt_quiz)
    quiz = res_quiz.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="الاختبار غير موجود.")

    # Check allowed attempts
    if quiz.allowed_attempts > 0:
        stmt_count = select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.student_id == student_id)
        res_count = await db.execute(stmt_count)
        attempts = res_count.scalars().all()
        if len(attempts) >= quiz.allowed_attempts:
            raise HTTPException(
                status_code=400,
                detail=f"لقد استنفدت عدد المحاولات المتاحة لهذا الاختبار ({quiz.allowed_attempts} محاولات)."
            )

    # Fetch questions
    stmt_qq = select(Question, QuizQuestion.points_override).join(
        QuizQuestion, QuizQuestion.question_id == Question.id
    ).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order)
    res_qq = await db.execute(stmt_qq)
    qq_rows = res_qq.all()

    if not qq_rows:
        raise HTTPException(status_code=400, detail="الاختبار لا يحتوي على أسئلة حالياً.")

    # Prepare questions snapshot
    questions_snapshot = []
    for question, pts_override in qq_rows:
        stmt_opts = select(QuestionOption).where(QuestionOption.question_id == question.id).order_by(QuestionOption.order)
        res_opts = await db.execute(stmt_opts)
        options = res_opts.scalars().all()

        opts_data = []
        for opt in options:
            opts_data.append({
                "id": opt.id,
                "text": opt.option_text,
                "order": opt.order
            })

        if quiz.shuffle_options:
            random.shuffle(opts_data)

        questions_snapshot.append({
            "id": question.id,
            "title": question.title,
            "text": question.question_text,
            "type": question.question_type,
            "points": pts_override if pts_override is not None else question.points,
            "options": opts_data,
            "image_url": question.image_url
        })

    if quiz.shuffle_questions:
        random.shuffle(questions_snapshot)

    attempt_number = len(attempts) + 1 if quiz.allowed_attempts > 0 else 1
    new_attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=student_id,
        attempt_number=attempt_number,
        status="in_progress",
        start_time=datetime.utcnow(),
        questions_snapshot=questions_snapshot
    )
    db.add(new_attempt)
    await db.flush()

    for q_snap in questions_snapshot:
        q_attempt = QuizAttemptQuestion(
            attempt_id=new_attempt.id,
            question_id=q_snap["id"],
            question_snapshot=q_snap,
            points_awarded=0.0,
            is_correct=False
        )
        db.add(q_attempt)

    await db.commit()
    await db.refresh(new_attempt)
    return new_attempt

async def submit_quiz_attempt(
    db: AsyncSession,
    attempt_id: str,
    student_id: str,
    answers: List[Dict[str, Any]] # [{question_id: str, selected_option_ids: [], text_answer: str}]
) -> QuizAttempt:
    stmt_att = select(QuizAttempt).where(QuizAttempt.id == attempt_id, QuizAttempt.student_id == student_id)
    res_att = await db.execute(stmt_att)
    attempt = res_att.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="محاولة الاختبار غير موجودة.")

    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="تم تسليم هذه المحاولة من قبل.")

    stmt_quiz = select(Quiz).where(Quiz.id == attempt.quiz_id)
    res_quiz = await db.execute(stmt_quiz)
    quiz = res_quiz.scalar_one_or_none()

    # Check time limit
    if quiz.time_limit_minutes > 0:
        elapsed = datetime.utcnow() - attempt.start_time
        if elapsed.total_seconds() > (quiz.time_limit_minutes * 60 + 30):
            attempt.status = "timed_out"

    total_possible = 0.0
    total_awarded = 0.0

    # Fetch attempt questions
    stmt_aq = select(QuizAttemptQuestion).where(QuizAttemptQuestion.attempt_id == attempt_id)
    res_aq = await db.execute(stmt_aq)
    aq_list = res_aq.scalars().all()

    answers_dict = {a["question_id"]: a for a in answers}

    for aq in aq_list:
        q_id = aq.question_id
        q_snap = aq.question_snapshot
        q_pts = q_snap.get("points", 1.0)
        total_possible += q_pts

        ans = answers_dict.get(q_id, {})
        sel_opts = ans.get("selected_option_ids", [])
        txt_ans = ans.get("text_answer", "")

        # Save student answer
        sa = StudentAnswer(
            attempt_question_id=aq.id,
            selected_option_ids=sel_opts,
            text_answer=txt_ans
        )
        db.add(sa)

        # Grade single_mcq & true_false automatically
        stmt_correct = select(QuestionOption.id).where(QuestionOption.question_id == q_id, QuestionOption.is_correct == True)
        res_correct = await db.execute(stmt_correct)
        correct_ids = [c for (c,) in res_correct.all()]

        is_correct = False
        points_awarded = 0.0

        if sel_opts and set(sel_opts) == set(correct_ids):
            is_correct = True
            points_awarded = q_pts

        aq.is_correct = is_correct
        aq.points_awarded = points_awarded
        total_awarded += points_awarded

    attempt.score = round(total_awarded, 2)
    attempt.percentage = round((total_awarded / total_possible * 100.0) if total_possible > 0 else 0.0, 2)
    attempt.passed = attempt.percentage >= quiz.passing_score
    attempt.status = "submitted" if attempt.status != "timed_out" else "timed_out"
    attempt.end_time = datetime.utcnow()
    attempt.submitted_at = datetime.utcnow()

    # Update lesson progress if attached
    if quiz.lesson_id:
        stmt_lp = select(LessonProgress).where(
            LessonProgress.student_id == student_id,
            LessonProgress.lesson_id == quiz.lesson_id
        )
        res_lp = await db.execute(stmt_lp)
        lp = res_lp.scalar_one_or_none()
        if lp:
            if attempt.percentage > lp.best_quiz_score:
                lp.best_quiz_score = attempt.percentage
            if attempt.passed:
                lp.quiz_passed = True

    await db.commit()
    await db.refresh(attempt)
    return attempt
