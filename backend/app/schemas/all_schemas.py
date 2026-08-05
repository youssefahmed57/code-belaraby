import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr, model_validator, ConfigDict

# User & Auth Schemas
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

# Course & Content Schemas
class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    description: Optional[str] = ""
    grade_level: str
    price: float
    instructor_name: Optional[str] = "يوسف أحمد صبحي عابدين"
    is_published: Optional[bool] = True

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

# Payment Schemas
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
    status: str
    payment_method: str
    receipt_url: Optional[str] = None
    transaction_reference: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_payment_fields(cls, values: Any) -> Any:
        if hasattr(values, "__dict__"):
            v = values.__dict__
            if not getattr(values, "user_id", None) and getattr(values, "student_id", None):
                values.user_id = values.student_id
            if not getattr(values, "amount", None) and getattr(values, "amount_paid", None):
                values.amount = values.amount_paid
        elif isinstance(values, dict):
            if not values.get("user_id") and values.get("student_id"):
                values["user_id"] = values["student_id"]
            if not values.get("amount") and values.get("amount_paid"):
                values["amount"] = values["amount_paid"]
        return values

# Code Execution Schemas
class RunCodeRequest(BaseModel):
    language: str = Field(...)
    code: Optional[str] = None
    source_code: Optional[str] = None
    stdin: Optional[str] = ""

    @model_validator(mode="before")
    @classmethod
    def resolve_code(cls, values: Any) -> Any:
        if isinstance(values, dict):
            c = values.get("code") or values.get("source_code") or ""
            values["code"] = c
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

# Quiz Schemas
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
    correct_count: Optional[int] = 0
    total_questions: Optional[int] = 0
