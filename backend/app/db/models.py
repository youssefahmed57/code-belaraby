import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Enum, JSON, Table, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    public_id = Column(String(36), unique=True, index=True, default=generate_uuid)
    arabic_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    grade_level = Column(String(50), nullable=False, default="first_secondary") # first_secondary, second_secondary, beginner
    parent_name = Column(String(255), nullable=True)
    parent_phone = Column(String(50), nullable=True)
    status = Column(String(50), default="active", nullable=False) # pending, active, suspended, disabled
    avatar_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    enrolments = relationship("Enrolment", back_populates="student", foreign_keys="Enrolment.student_id")
    payments = relationship("Payment", back_populates="student", foreign_keys="Payment.student_id")
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    submissions = relationship("CodeSubmission", back_populates="student")

class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False) # student, instructor, admin, super_admin
    description = Column(String(255), nullable=True)

    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission")

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    short_description = Column(Text, nullable=False)
    full_description = Column(Text, nullable=False)
    grade_level = Column(String(50), nullable=False) # first_secondary, second_secondary, beginner
    cover_image = Column(Text, nullable=True)
    trailer_video_url = Column(Text, nullable=True)
    instructor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    discount_price = Column(Float, nullable=True)
    duration_hours = Column(Float, default=10.0)
    estimated_learning_hours = Column(Float, default=15.0)
    requirements = Column(JSON, default=list)
    learning_outcomes = Column(JSON, default=list)
    status = Column(String(50), default="published", nullable=False) # draft, published, archived
    visibility = Column(String(50), default="public", nullable=False) # public, private
    access_duration_days = Column(Integer, default=365)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order")
    enrolments = relationship("Enrolment", back_populates="course")

class CourseInstructor(Base):
    __tablename__ = "course_instructors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    instructor_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_title = Column(String(100), default="محاضر رئيسي")

class Module(Base):
    __tablename__ = "modules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="published", nullable=False)
    unit_exam_id = Column(String(36), nullable=True)
    unlock_rules = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    module_id = Column(String(36), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    learning_objectives = Column(JSON, default=list)
    rich_content = Column(Text, nullable=True)
    video_asset_id = Column(String(36), ForeignKey("video_assets.id"), nullable=True)
    estimated_duration_minutes = Column(Integer, default=30)
    order = Column(Integer, default=1, nullable=False)
    passing_score = Column(Float, default=70.0)
    preview_status = Column(Boolean, default=False)
    publishing_status = Column(String(50), default="published")
    required_video_percentage = Column(Float, default=80.0)
    required_practical_submission = Column(Boolean, default=True)
    required_quiz_pass = Column(Boolean, default=True)
    release_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    module = relationship("Module", back_populates="lessons")
    video_asset = relationship("VideoAsset")
    blocks = relationship("LessonBlock", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonBlock.order")
    files = relationship("LessonFile", back_populates="lesson", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="lesson")
    coding_problems = relationship("CodingProblem", back_populates="lesson")

class LessonBlock(Base):
    __tablename__ = "lesson_blocks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False) # intro, objective, theory, video, example, compiler, challenge, file, summary, quiz
    content = Column(JSON, nullable=False)
    order = Column(Integer, default=1, nullable=False)

    lesson = relationship("Lesson", back_populates="blocks")

class LessonPrerequisite(Base):
    __tablename__ = "lesson_prerequisites"

    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    prerequisite_lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)

class LessonFile(Base):
    __tablename__ = "lesson_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    file_key = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), default="application/octet-stream")
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    lesson = relationship("Lesson", back_populates="files")

class VideoAsset(Base):
    __tablename__ = "video_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    provider = Column(String(50), default="cloudflare_stream") # cloudflare_stream, local
    external_video_id = Column(String(255), nullable=False)
    duration_seconds = Column(Integer, default=0)
    hls_url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Enrolment(Base):
    __tablename__ = "enrolments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="active", nullable=False) # pending, active, paused, expired, revoked, completed
    access_start = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_expiry = Column(DateTime, nullable=True)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=True)
    source = Column(String(50), default="manual_payment") # manual_payment, admin_assignment, coupon
    approved_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = relationship("User", foreign_keys=[student_id], back_populates="enrolments")
    course = relationship("Course", back_populates="enrolments")
    payment = relationship("Payment", foreign_keys=[payment_id])

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    reference_code = Column(String(100), unique=True, index=True, nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    amount_expected = Column(Float, nullable=False)
    amount_submitted = Column(Float, nullable=True)
    payment_method = Column(String(50), nullable=False) # instapay, vodafone_cash, whatsapp
    sender_identifier = Column(String(100), nullable=True)
    receipt_file_key = Column(String(500), nullable=True)
    student_note = Column(Text, nullable=True)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    review_note = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    status = Column(String(50), default="draft", nullable=False) # draft, awaiting_receipt, pending_review, more_info_required, approved, rejected, cancelled, refunded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    student = relationship("User", foreign_keys=[student_id], back_populates="payments")
    course = relationship("Course")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    events = relationship("PaymentEvent", back_populates="payment", cascade="all, delete-orphan")

class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    payment = relationship("Payment", back_populates="events")

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=True)
    passing_score = Column(Float, default=70.0, nullable=False)
    time_limit_minutes = Column(Integer, default=15, nullable=False) # 0 for no limit
    allowed_attempts = Column(Integer, default=3, nullable=False) # 0 for unlimited
    shuffle_questions = Column(Boolean, default=True)
    shuffle_options = Column(Boolean, default=True)
    show_answers_mode = Column(String(50), default="after_submission") # immediately, after_submission, after_deadline
    keep_score_mode = Column(String(50), default="highest") # highest, latest
    negative_marking = Column(Boolean, default=False)
    availability_start = Column(DateTime, nullable=True)
    availability_end = Column(DateTime, nullable=True)
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lesson = relationship("Lesson", back_populates="quizzes")
    quiz_questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=True)
    title = Column(String(255), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False) # single_mcq, multi_mcq, true_false, fill_blank, short_answer, essay, arrange_steps, match, predict_output, find_error, complete_code, image_based
    difficulty = Column(String(50), default="medium")
    topic = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    points = Column(Float, default=1.0)
    explanation = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", order_by="QuestionOption.order")

class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    order = Column(Integer, default=1)
    match_pair = Column(Text, nullable=True)

    question = relationship("Question", back_populates="options")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    order = Column(Integer, default=1)
    points_override = Column(Float, nullable=True)

    quiz = relationship("Quiz", back_populates="quiz_questions")
    question = relationship("Question")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="in_progress") # in_progress, submitted, timed_out, reviewed
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    score = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    questions_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("User", back_populates="quiz_attempts")
    attempt_questions = relationship("QuizAttemptQuestion", back_populates="attempt", cascade="all, delete-orphan")

class QuizAttemptQuestion(Base):
    __tablename__ = "quiz_attempt_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    attempt_id = Column(String(36), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id"), nullable=False)
    question_snapshot = Column(JSON, nullable=False)
    points_awarded = Column(Float, default=0.0)
    is_correct = Column(Boolean, default=False)
    feedback = Column(Text, nullable=True)

    attempt = relationship("QuizAttempt", back_populates="attempt_questions")
    student_answer = relationship("StudentAnswer", uselist=False, back_populates="attempt_question", cascade="all, delete-orphan")

class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    attempt_question_id = Column(String(36), ForeignKey("quiz_attempt_questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_ids = Column(JSON, default=list)
    text_answer = Column(Text, nullable=True)
    array_answer = Column(JSON, default=list)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    attempt_question = relationship("QuizAttemptQuestion", back_populates="student_answer")

class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    arabic_statement = Column(Text, nullable=False)
    difficulty = Column(String(50), default="easy") # easy, medium, hard
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=True)
    supported_languages = Column(JSON, default=lambda: ["python", "javascript", "html_css_js"])
    starter_code = Column(JSON, default=dict)
    function_signature = Column(Text, nullable=True)
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    examples = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)
    time_limit_seconds = Column(Float, default=2.0)
    memory_limit_mb = Column(Integer, default=128)
    points = Column(Integer, default=10)
    status = Column(String(50), default="published")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lesson = relationship("Lesson", back_populates="coding_problems")
    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan", order_by="TestCase.order")
    submissions = relationship("CodeSubmission", back_populates="problem", cascade="all, delete-orphan")

class CodingProblemLanguage(Base):
    __tablename__ = "coding_problem_languages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    problem_id = Column(String(36), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(50), nullable=False) # python, javascript, html_css_js
    starter_code = Column(Text, nullable=False)
    solution_code = Column(Text, nullable=True)

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    problem_id = Column(String(36), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False)
    input_data = Column(Text, nullable=False, default="")
    expected_output = Column(Text, nullable=False, default="")
    is_public = Column(Boolean, default=True)
    order = Column(Integer, default=1)
    explanation = Column(Text, nullable=True)

    problem = relationship("CodingProblem", back_populates="test_cases")

class CodeDraft(Base):
    __tablename__ = "code_drafts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=True)
    problem_id = Column(String(36), ForeignKey("coding_problems.id"), nullable=True)
    language = Column(String(50), nullable=False, default="python")
    code = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", "problem_id", "language", name="uq_student_draft"),
    )

class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id = Column(String(36), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=True)
    language = Column(String(50), nullable=False, default="python")
    source_code = Column(Text, nullable=False)
    status = Column(String(50), default="queued") # queued, running, accepted, wrong_answer, compilation_error, runtime_error, time_limit_exceeded, memory_limit_exceeded, internal_error
    score = Column(Float, default=0.0)
    execution_time_seconds = Column(Float, default=0.0)
    memory_used_kb = Column(Integer, default=0)
    passed_test_cases = Column(Integer, default=0)
    total_test_cases = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("User", back_populates="submissions")
    problem = relationship("CodingProblem", back_populates="submissions")
    test_results = relationship("SubmissionTestResult", back_populates="submission", cascade="all, delete-orphan")

class SubmissionTestResult(Base):
    __tablename__ = "submission_test_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("code_submissions.id", ondelete="CASCADE"), nullable=False)
    test_case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=False)
    is_passed = Column(Boolean, default=False)
    status = Column(String(50), default="accepted")
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    execution_time_seconds = Column(Float, default=0.0)
    memory_used_kb = Column(Integer, default=0)

    submission = relationship("CodeSubmission", back_populates="test_results")

class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="locked") # locked, available, in_progress, completed
    theory_opened = Column(Boolean, default=False)
    theory_completed = Column(Boolean, default=False)
    video_watched_percentage = Column(Float, default=0.0)
    video_completed = Column(Boolean, default=False)
    practical_submitted = Column(Boolean, default=False)
    practical_passed = Column(Boolean, default=False)
    quiz_passed = Column(Boolean, default=False)
    best_quiz_score = Column(Float, default=0.0)
    manual_override = Column(Boolean, default=False)
    manual_override_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    override_reason = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson_progress"),
    )

class VideoProgress(Base):
    __tablename__ = "video_progress"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    video_asset_id = Column(String(36), ForeignKey("video_assets.id"), nullable=False)
    first_watched_at = Column(DateTime, default=datetime.utcnow)
    last_watched_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_playback_position = Column(Float, default=0.0)
    total_watched_seconds = Column(Float, default=0.0)
    completion_percentage = Column(Float, default=0.0)
    session_count = Column(Integer, default=1)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", "video_asset_id", name="uq_student_video_progress"),
    )

class CourseProgress(Base):
    __tablename__ = "course_progress"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    completion_percentage = Column(Float, default=0.0)
    total_completed_lessons = Column(Integer, default=0)
    total_lessons = Column(Integer, default=0)
    last_activity_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_progress"),
    )

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=True)
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="open") # open, in_progress, answered, closed
    assigned_instructor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("SupportMessage", back_populates="ticket", cascade="all, delete-orphan", order_by="SupportMessage.created_at")

class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    ticket_id = Column(String(36), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    attachment_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("SupportTicket", back_populates="messages")
    sender = relationship("User")

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    target_type = Column(String(50), default="platform") # platform, course
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=True)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info") # payment, lesson, quiz, support, announcement
    is_read = Column(Boolean, default=False)
    link_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    updated_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class AdminNote(Base):
    __tablename__ = "admin_notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    target_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
