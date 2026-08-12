from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.db.models import CodeSubmission, LessonProgress, SubmissionTestResult, TestCase, User
from app.schemas.all_schemas import ExecutionResponse, RunCodeRequest, SubmitProblemRequest
from app.services.access_service import require_accessible_problem
from app.services.execution_service import (
    ExecutionProviderUnavailable,
    SUPPORTED_EXECUTION_LANGUAGES,
    execute_code_sandboxed,
)
from app.services.unlock_service import evaluate_lesson_completion


router = APIRouter(prefix="/coding-problems", tags=["Coding Execution"])


@router.post("/run", response_model=ExecutionResponse)
async def run_playground_code(
    req: RunCodeRequest,
    current_user: User = Depends(get_current_user),
):
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="الحساب غير مفعل.")

    if req.language.lower() not in SUPPORTED_EXECUTION_LANGUAGES:
        raise HTTPException(status_code=400, detail="اللغة المطلوبة غير مدعومة.")

    try:
        result = await execute_code_sandboxed(
            language=req.language,
            source_code=req.code or "",
            stdin_data=req.stdin or "",
            time_limit_seconds=2.0,
        )
    except ExecutionProviderUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="خدمة تشغيل الأكواد المعزولة غير متاحة حالياً.",
        ) from exc

    return ExecutionResponse(
        status=result["status"],
        stdout=result["stdout"],
        stderr=result["stderr"],
        execution_time_seconds=result["execution_time_seconds"],
        memory_used_kb=result["memory_used_kb"],
    )


@router.post("/submit", response_model=ExecutionResponse)
async def submit_problem_solution(
    req: SubmitProblemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="الحساب غير مفعل.")

    problem, lesson = await require_accessible_problem(
        db=db,
        student_id=current_user.id,
        problem_id=req.problem_id,
        requested_language=req.language,
    )

    test_cases = (
        await db.execute(
            select(TestCase).where(TestCase.problem_id == problem.id).order_by(TestCase.order)
        )
    ).scalars().all()

    submission = CodeSubmission(
        student_id=current_user.id,
        problem_id=problem.id,
        lesson_id=lesson.id,
        language=req.language.lower(),
        source_code=req.code,
        status="running",
        total_test_cases=len(test_cases),
    )
    db.add(submission)
    await db.flush()

    passed_count = 0
    total_time = 0.0
    final_status = "Accepted"

    for test_case in test_cases:
        try:
            execution_result = await execute_code_sandboxed(
                language=req.language,
                source_code=req.code,
                stdin_data=test_case.input_data,
                expected_output=test_case.expected_output,
                time_limit_seconds=problem.time_limit_seconds,
                memory_limit_mb=problem.memory_limit_mb,
            )
        except ExecutionProviderUnavailable as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="خدمة تشغيل الأكواد المعزولة غير متاحة حالياً.",
            ) from exc

        total_time += execution_result["execution_time_seconds"]
        is_passed = (
            execution_result["status"] == "Accepted"
            and execution_result["stdout"].strip() == test_case.expected_output.strip()
        )

        if is_passed:
            passed_count += 1
        elif final_status == "Accepted":
            final_status = execution_result["status"]

        db.add(
            SubmissionTestResult(
                submission_id=submission.id,
                test_case_id=test_case.id,
                is_passed=is_passed,
                status="accepted" if is_passed else final_status.lower().replace(" ", "_"),
                stdout=execution_result["stdout"] if test_case.is_public else "[hidden]",
                stderr=execution_result["stderr"] if test_case.is_public else "[hidden]",
                execution_time_seconds=execution_result["execution_time_seconds"],
                memory_used_kb=execution_result["memory_used_kb"],
            )
        )

    total_tests = len(test_cases)
    submission.status = "accepted" if passed_count == total_tests else final_status.lower().replace(" ", "_")
    submission.score = round((passed_count / total_tests) * 100.0, 2) if total_tests else 0.0
    submission.passed_test_cases = passed_count
    submission.execution_time_seconds = round(total_time, 3)

    lesson_progress = await db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    if not lesson_progress:
        lesson_progress = LessonProgress(student_id=current_user.id, lesson_id=lesson.id, status="in_progress")
        db.add(lesson_progress)

    lesson_progress.practical_submitted = True
    if passed_count == total_tests and total_tests > 0:
        lesson_progress.practical_passed = True

    await db.commit()
    await db.refresh(submission)

    await evaluate_lesson_completion(db, current_user.id, lesson.id)

    return ExecutionResponse(
        status=submission.status.upper(),
        stdout=f"تم اجتياز {passed_count} من أصل {total_tests} اختبارات.",
        stderr="",
        execution_time_seconds=submission.execution_time_seconds,
        memory_used_kb=0,
        passed_test_cases=passed_count,
        total_test_cases=total_tests,
    )
