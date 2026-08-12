from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserRegister(BaseModel):
    arabic_name: str
    phone_number: str
    password: str
    password_confirm: str
    grade_level: Optional[str] = "first_secondary"
    email: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_phone_number: Optional[str] = None


RegisterStudentRequest = UserRegister


class UserLogin(BaseModel):
    identifier: str
    password: str


LoginRequest = UserLogin


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    arabic_name: str
    phone_number: str
    role: Optional[str] = "student"
    grade_level: Optional[str] = None
    is_active: Optional[bool] = True


UserResponse = UserProfileResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    role: str


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    description: Optional[str] = ""
    short_description: Optional[str] = ""
    full_description: Optional[str] = ""
    grade_level: str
    price: float
    discount_price: Optional[float] = None
    instructor_name: Optional[str] = "يوسف أحمد صبحي عابدين"
    is_published: Optional[bool] = True

    @model_validator(mode="before")
    @classmethod
    def resolve_course_fields(cls, values: Any) -> Any:
        if hasattr(values, "__dict__"):
            short_description = getattr(values, "short_description", None) or ""
            full_description = getattr(values, "full_description", None) or ""
            values.short_description = short_description
            values.full_description = full_description
            values.description = getattr(values, "description", None) or short_description or full_description
            if getattr(values, "price", None) is not None:
                values.price = float(values.price)
            if getattr(values, "discount_price", None) is not None:
                values.discount_price = float(values.discount_price)
        elif isinstance(values, dict):
            short_description = values.get("short_description") or ""
            full_description = values.get("full_description") or ""
            values["short_description"] = short_description
            values["full_description"] = full_description
            values["description"] = values.get("description") or short_description or full_description
            if values.get("price") is not None:
                values["price"] = float(values["price"])
            if values.get("discount_price") is not None:
                values["discount_price"] = float(values["discount_price"])
        return values


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    summary: Optional[str] = ""
    video_url: Optional[str] = None
    theory_content: Optional[str] = None
    order: int
    is_preview: Optional[bool] = False
    module_id: str


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    order: int
    lessons: List[LessonResponse] = []


class PaymentOrderCreate(BaseModel):
    course_id: str
    payment_method: str = "instapay"


CreatePaymentRequest = PaymentOrderCreate


class SubmitReceiptRequest(BaseModel):
    payment_id: str
    transaction_reference: Optional[str] = None


class PaymentReviewRequest(BaseModel):
    payment_id: str
    action: str
    review_note: Optional[str] = None
    rejection_reason: Optional[str] = None


AdminReviewPaymentRequest = PaymentReviewRequest


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    student_id: Optional[str] = None
    course_id: str
    amount: Optional[float] = 0.0
    amount_paid: Optional[float] = 0.0
    amount_expected: Optional[float] = 0.0
    amount_submitted: Optional[float] = 0.0
    status: str
    payment_method: str
    receipt_url: Optional[str] = None
    receipt_file_key: Optional[str] = None
    reference_code: Optional[str] = None
    sender_identifier: Optional[str] = None
    student_note: Optional[str] = None
    created_at: Optional[Any] = None
    transaction_reference: Optional[str] = None
    amount_difference: Optional[float] = None
    amount_delta_status: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_payment_fields(cls, values: Any) -> Any:
        def _amount_delta(expected_value: Any, submitted_value: Any) -> tuple[Optional[float], Optional[str]]:
            if expected_value is None or submitted_value is None:
                return None, None
            delta = Decimal(str(submitted_value)) - Decimal(str(expected_value))
            if delta < 0:
                return float(delta), "underpaid"
            if delta > 0:
                return float(delta), "overpaid"
            return float(delta), "exact"

        if hasattr(values, "__dict__"):
            if not getattr(values, "user_id", None) and getattr(values, "student_id", None):
                values.user_id = values.student_id
            if not getattr(values, "amount", None) and getattr(values, "amount_paid", None):
                values.amount = values.amount_paid
            if getattr(values, "amount_expected", None) is not None:
                values.amount_expected = float(values.amount_expected)
            if getattr(values, "amount_submitted", None) is not None:
                values.amount_submitted = float(values.amount_submitted)
            delta, delta_status = _amount_delta(
                getattr(values, "amount_expected", None),
                getattr(values, "amount_submitted", None),
            )
            values.amount_difference = delta
            values.amount_delta_status = delta_status
        elif isinstance(values, dict):
            if not values.get("user_id") and values.get("student_id"):
                values["user_id"] = values["student_id"]
            if not values.get("amount") and values.get("amount_paid"):
                values["amount"] = values["amount_paid"]
            if values.get("amount_expected") is not None:
                values["amount_expected"] = float(values["amount_expected"])
            if values.get("amount_submitted") is not None:
                values["amount_submitted"] = float(values["amount_submitted"])
            delta, delta_status = _amount_delta(values.get("amount_expected"), values.get("amount_submitted"))
            values["amount_difference"] = delta
            values["amount_delta_status"] = delta_status
        return values


class RunCodeRequest(BaseModel):
    language: str = Field(...)
    code: Optional[str] = None
    source_code: Optional[str] = None
    stdin: Optional[str] = ""

    @model_validator(mode="before")
    @classmethod
    def resolve_code(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values["code"] = values.get("code") or values.get("source_code") or ""
        return values


class SubmitProblemRequest(BaseModel):
    problem_id: str
    lesson_id: Optional[str] = None
    language: str = Field(...)
    code: str = Field(...)


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    execution_time_seconds: float
    memory_used_kb: int
    passed_test_cases: Optional[int] = None
    total_test_cases: Optional[int] = None


class StartQuizResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    time_limit_minutes: int
    allowed_attempts: int
    questions: List[Dict[str, Any]]


class SubmitQuizRequest(BaseModel):
    attempt_id: str
    answers: List[Dict[str, Any]]


class QuizAttemptResultResponse(BaseModel):
    attempt_id: str
    score: float
    percentage: Optional[float] = 0.0
    passed: bool
    status: Optional[str] = "submitted"
    submitted_at: Optional[Any] = None
    correct_count: Optional[int] = 0
    total_questions: Optional[int] = 0
