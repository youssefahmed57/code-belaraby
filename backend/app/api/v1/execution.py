from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models import User, CodingProblem, TestCase, CodeSubmission, SubmissionTestResult, LessonProgress
from app.api.deps import get_current_user
from app.schemas.all_schemas import RunCodeRequest, SubmitProblemRequest, ExecutionResponse
from app.services.execution_service import execute_code_sandboxed
from app.services.unlock_service import evaluate_lesson_completion

router = APIRouter(prefix="/coding-problems", tags=["Coding Execution"])

@router.post("/run", response_model=ExecutionResponse)
async def run_playground_code(
    req: RunCodeRequest,
    current_user: User = Depends(get_current_user)
):
    result = execute_code_sandboxed(
        language=req.language,
        source_code=req.code,
        stdin_data=req.stdin or "",
        time_limit_seconds=2.0
    )
    return ExecutionResponse(
        status=result["status"],
        stdout=result["stdout"],
        stderr=result["stderr"],
        execution_time_seconds=result["execution_time_seconds"],
        memory_used_kb=result["memory_used_kb"]
    )

@router.post("/submit", response_model=ExecutionResponse)
async def submit_problem_solution(
    req: SubmitProblemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_prob = select(CodingProblem).where(CodingProblem.id == req.problem_id)
    res_prob = await db.execute(stmt_prob)
    prob = res_prob.scalar_one_or_none()
    if not prob:
        raise HTTPException(status_code=404, detail="المسألة غير موجودة.")

    # Fetch test cases
    stmt_tc = select(TestCase).where(TestCase.problem_id == req.problem_id).order_by(TestCase.order)
    res_tc = await db.execute(stmt_tc)
    test_cases = res_tc.scalars().all()

    passed_count = 0
    total_count = len(test_cases)
    final_status = "Accepted"
    total_time = 0.0

    submission = CodeSubmission(
        student_id=current_user.id,
        problem_id=req.problem_id,
        lesson_id=req.lesson_id or prob.lesson_id,
        language=req.language,
        source_code=req.code,
        status="running",
        total_test_cases=total_count
    )
    db.add(submission)
    await db.flush()

    for tc in test_cases:
        res = execute_code_sandboxed(
            language=req.language,
            source_code=req.code,
            stdin_data=tc.input_data,
            time_limit_seconds=prob.time_limit_seconds
        )
        total_time += res["execution_time_seconds"]

        expected_clean = tc.expected_output.strip()
        actual_clean = res["stdout"].strip()

        is_passed = (res["status"] == "Accepted") and (expected_clean == actual_clean)

        if is_passed:
            passed_count += 1
        else:
            if final_status == "Accepted":
                final_status = res["status"] if res["status"] != "Accepted" else "Wrong Answer"

        db.add(SubmissionTestResult(
            submission_id=submission.id,
            test_case_id=tc.id,
            is_passed=is_passed,
            status="accepted" if is_passed else final_status,
            stdout=res["stdout"] if tc.is_public else "[مخفي]",
            stderr=res["stderr"] if tc.is_public else "[مخفي]",
            execution_time_seconds=res["execution_time_seconds"]
        ))

    score = round((passed_count / total_count * 100.0) if total_count > 0 else 0.0, 2)
    submission.status = "accepted" if passed_count == total_count else final_status.lower().replace(" ", "_")
    submission.score = score
    submission.passed_test_cases = passed_count
    submission.execution_time_seconds = round(total_time, 3)

    # Update lesson progress if attached
    target_lesson_id = req.lesson_id or prob.lesson_id
    if target_lesson_id:
        stmt_lp = select(LessonProgress).where(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == target_lesson_id
        )
        res_lp = await db.execute(stmt_lp)
        lp = res_lp.scalar_one_or_none()
        if lp:
            lp.practical_submitted = True
            if passed_count == total_count:
                lp.practical_passed = True

    await db.commit()
    await db.refresh(submission)

    if target_lesson_id:
        await evaluate_lesson_completion(db, current_user.id, target_lesson_id)

    return ExecutionResponse(
        status=submission.status.upper(),
        stdout=f"تم اجتياز {passed_count} من أصل {total_count} اختبارات.",
        stderr="",
        execution_time_seconds=submission.execution_time_seconds,
        memory_used_kb=15000,
        passed_test_cases=passed_count,
        total_test_cases=total_count
    )
