import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
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


def _validate_execution_payload(language: str, source_code: str, stdin: str = "", problem_id: str | None = None) -> None:
    normalized_language = (language or "").strip().lower()
    if not normalized_language or len(normalized_language) > settings.MAX_EXECUTION_LANGUAGE_LENGTH:
        raise HTTPException(status_code=422, detail="قيمة اللغة المطلوبة غير صالحة.")
    if normalized_language not in SUPPORTED_EXECUTION_LANGUAGES:
        raise HTTPException(status_code=400, detail="اللغة المطلوبة غير مدعومة.")
    if len((source_code or "").encode("utf-8")) > settings.MAX_EXECUTION_SOURCE_BYTES:
        raise HTTPException(status_code=413, detail="حجم الكود المرسل يتجاوز الحد الأقصى المسموح به.")
    if len((stdin or "").encode("utf-8")) > settings.MAX_EXECUTION_STDIN_BYTES:
        raise HTTPException(status_code=413, detail="حجم بيانات الإدخال يتجاوز الحد الأقصى المسموح به.")
    if problem_id is not None and len(problem_id) > settings.MAX_EXECUTION_PROBLEM_ID_LENGTH:
        raise HTTPException(status_code=422, detail="معرف المسألة غير صالح.")


@router.post("/run", response_model=ExecutionResponse)
async def run_playground_code(
    req: RunCodeRequest,
    current_user: User = Depends(get_current_user),
):
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="الحساب غير مفعل.")

    _validate_execution_payload(req.language, req.code or "", req.stdin or "")

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

    _validate_execution_payload(req.language, req.code, problem_id=req.problem_id)
    problem, lesson = await require_accessible_problem(
        db=db,
        student_id=current_user.id,
        problem_id=req.problem_id,
        requested_language=req.language,
    )

    test_cases = (
        await db.execute(select(TestCase).where(TestCase.problem_id == problem.id).order_by(TestCase.order))
    ).scalars().all()
    if len(test_cases) > settings.MAX_EXECUTION_TEST_CASES_PER_REQUEST:
        raise HTTPException(
            status_code=422,
            detail="عدد حالات الاختبار لهذه المسألة يتجاوز الحد الآمن للتنفيذ المباشر عبر الطلب الحالي.",
        )

    max_request_budget = settings.MAX_EXECUTION_REQUEST_DEADLINE_SECONDS
    worst_case_budget = len(test_cases) * max(problem.time_limit_seconds, 1)
    if worst_case_budget > max_request_budget:
        raise HTTPException(
            status_code=422,
            detail="تنفيذ هذه المسألة يتطلب زمناً أطول من الحد المسموح به للطلب المباشر.",
        )

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

    deadline = time.monotonic() + settings.MAX_EXECUTION_REQUEST_DEADLINE_SECONDS
    passed_count = 0
    total_time = 0.0
    final_status = "Accepted"

    for test_case in test_cases:
        if time.monotonic() >= deadline:
            raise HTTPException(
                status_code=503,
                detail="تم إيقاف التنفيذ لأن الطلب تجاوز المهلة القصوى المسموح بها.",
            )
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
