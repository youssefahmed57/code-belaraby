"""Initial frozen schema migration.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-08-01 20:30:00.000000

This revision intentionally contains an explicit schema snapshot instead of
importing live ORM metadata. Fresh databases must be reproducible from the
Alembic history alone.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


TABLE_DROP_ORDER = [
    "student_answers",
    "submission_test_results",
    "quiz_attempt_questions",
    "test_cases",
    "support_messages",
    "quiz_questions",
    "quiz_attempts",
    "question_options",
    "coding_problem_languages",
    "code_submissions",
    "code_drafts",
    "assignment_submissions",
    "video_progress",
    "support_tickets",
    "quizzes",
    "questions",
    "lesson_progress",
    "lesson_prerequisites",
    "lesson_files",
    "lesson_blocks",
    "coding_problems",
    "assignments",
    "payment_events",
    "lessons",
    "enrolments",
    "coupon_usages",
    "payments",
    "modules",
    "course_progress",
    "course_instructors",
    "coupons",
    "certificates",
    "announcements",
    "user_sessions",
    "user_roles",
    "user_badges",
    "role_permissions",
    "platform_settings",
    "password_reset_tokens",
    "notifications",
    "courses",
    "audit_logs",
    "admin_notes",
    "video_assets",
    "users",
    "roles",
    "permissions",
    "badges",
]


def upgrade() -> None:
    op.create_table(
        "badges",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("title_arabic", sa.String(length=255), nullable=False),
        sa.Column("description_arabic", sa.Text(), nullable=False),
        sa.Column("icon_name", sa.String(length=100)),
        sa.Column("xp_reward", sa.Integer()),
    )
    op.create_index("ix_badges_code", "badges", ["code"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255)),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("public_id", sa.String(length=36), unique=True),
        sa.Column("arabic_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("grade_level", sa.String(length=50), nullable=False),
        sa.Column("parent_name", sa.String(length=255)),
        sa.Column("parent_phone", sa.String(length=50)),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("avatar_url", sa.Text()),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime()),
        sa.Column("xp_points", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_public_id", "users", ["public_id"], unique=True)
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)

    op.create_table(
        "video_assets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=50)),
        sa.Column("external_video_id", sa.String(length=255), nullable=False),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("hls_url", sa.Text()),
        sa.Column("thumbnail_url", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "admin_notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("target_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=255)),
        sa.Column("details", sa.JSON()),
        sa.Column("ip_address", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "courses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("full_description", sa.Text(), nullable=False),
        sa.Column("grade_level", sa.String(length=50), nullable=False),
        sa.Column("cover_image", sa.Text()),
        sa.Column("trailer_video_url", sa.Text()),
        sa.Column("instructor_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount_price", sa.Numeric(precision=12, scale=2)),
        sa.Column("duration_hours", sa.Float()),
        sa.Column("estimated_learning_hours", sa.Float()),
        sa.Column("requirements", sa.JSON()),
        sa.Column("learning_outcomes", sa.JSON()),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("visibility", sa.String(length=50), nullable=False),
        sa.Column("unlock_mode", sa.String(length=50), nullable=False),
        sa.Column("access_duration_days", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_courses_slug", "courses", ["slug"], unique=True)

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=50)),
        sa.Column("is_read", sa.Boolean()),
        sa.Column("link_url", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_password_reset_tokens_token", "password_reset_tokens", ["token"], unique=True)

    op.create_table(
        "platform_settings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("updated_by_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_platform_settings_key", "platform_settings", ["key"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(length=36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.String(length=36), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "user_badges",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("badge_id", sa.String(length=36), sa.ForeignKey("badges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.String(length=36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("ip_address", sa.String(length=50)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_sessions_session_token", "user_sessions", ["session_token"], unique=True)

    op.create_table(
        "announcements",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("target_type", sa.String(length=50)),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id")),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "certificates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("certificate_code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("completion_grade", sa.Float(), nullable=False),
        sa.Column("student_name_arabic", sa.String(length=255), nullable=False),
        sa.Column("course_title_arabic", sa.String(length=255), nullable=False),
        sa.Column("qr_code_url", sa.Text()),
    )
    op.create_index("ix_certificates_certificate_code", "certificates", ["certificate_code"], unique=True)

    op.create_table(
        "coupons",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("discount_type", sa.String(length=20), nullable=False),
        sa.Column("discount_value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime()),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("current_uses", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE")),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_coupons_code", "coupons", ["code"], unique=True)

    op.create_table(
        "course_instructors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instructor_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_title", sa.String(length=100)),
    )

    op.create_table(
        "course_progress",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completion_percentage", sa.Float()),
        sa.Column("total_completed_lessons", sa.Integer()),
        sa.Column("total_lessons", sa.Integer()),
        sa.Column("last_activity_at", sa.DateTime()),
        sa.UniqueConstraint("student_id", "course_id", name="uq_student_course_progress"),
    )

    op.create_table(
        "modules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("unit_exam_id", sa.String(length=36)),
        sa.Column("unlock_rules", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_modules_course_id", "modules", ["course_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("reference_code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_expected", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("amount_submitted", sa.Numeric(precision=12, scale=2)),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("sender_identifier", sa.String(length=100)),
        sa.Column("receipt_file_key", sa.String(length=500)),
        sa.Column("receipt_hash", sa.String(length=64)),
        sa.Column("student_note", sa.Text()),
        sa.Column("reviewer_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("review_note", sa.Text()),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime()),
        sa.Column("reviewed_at", sa.DateTime()),
    )
    op.create_index("ix_payments_receipt_hash", "payments", ["receipt_hash"])
    op.create_index("ix_payments_course_id", "payments", ["course_id"])
    op.create_index("ix_payments_reference_code", "payments", ["reference_code"], unique=True)
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_student_id", "payments", ["student_id"])

    op.create_table(
        "coupon_usages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("coupon_id", sa.String(length=36), sa.ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_id", sa.String(length=36), sa.ForeignKey("payments.id")),
        sa.Column("discount_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("coupon_id", "student_id", name="uq_coupon_student_usage"),
    )

    op.create_table(
        "enrolments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("access_start", sa.DateTime(), nullable=False),
        sa.Column("access_expiry", sa.DateTime()),
        sa.Column("payment_id", sa.String(length=36), sa.ForeignKey("payments.id")),
        sa.Column("source", sa.String(length=50)),
        sa.Column("approved_by_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("student_id", "course_id", name="uq_enrolment_student_course"),
    )
    op.create_index("ix_enrolments_course_id", "enrolments", ["course_id"])
    op.create_index("ix_enrolments_student_id", "enrolments", ["student_id"])
    op.create_index("ix_enrolments_status", "enrolments", ["status"])

    op.create_table(
        "lessons",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("module_id", sa.String(length=36), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("learning_objectives", sa.JSON()),
        sa.Column("rich_content", sa.Text()),
        sa.Column("video_asset_id", sa.String(length=36), sa.ForeignKey("video_assets.id")),
        sa.Column("estimated_duration_minutes", sa.Integer()),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("passing_score", sa.Float()),
        sa.Column("preview_status", sa.Boolean()),
        sa.Column("publishing_status", sa.String(length=50)),
        sa.Column("required_video_percentage", sa.Float()),
        sa.Column("required_practical_submission", sa.Boolean()),
        sa.Column("required_quiz_pass", sa.Boolean()),
        sa.Column("release_date", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_lessons_module_id", "lessons", ["module_id"])
    op.create_index("ix_lessons_slug", "lessons", ["slug"])

    op.create_table(
        "payment_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("payment_id", sa.String(length=36), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_status", sa.String(length=50)),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("actor_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "assignments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.String(length=36), sa.ForeignKey("modules.id")),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id")),
        sa.Column("due_date", sa.DateTime()),
        sa.Column("max_score", sa.Float()),
        sa.Column("rubric", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "coding_problems",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("arabic_statement", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=50)),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.String(length=36), sa.ForeignKey("modules.id")),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id")),
        sa.Column("supported_languages", sa.JSON()),
        sa.Column("starter_code", sa.JSON()),
        sa.Column("function_signature", sa.Text()),
        sa.Column("input_format", sa.Text()),
        sa.Column("output_format", sa.Text()),
        sa.Column("constraints", sa.Text()),
        sa.Column("examples", sa.JSON()),
        sa.Column("explanation", sa.Text()),
        sa.Column("time_limit_seconds", sa.Float()),
        sa.Column("memory_limit_mb", sa.Integer()),
        sa.Column("points", sa.Integer()),
        sa.Column("status", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "lesson_blocks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
    )

    op.create_table(
        "lesson_files",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_key", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.Integer()),
        sa.Column("mime_type", sa.String(length=100)),
        sa.Column("is_public", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "lesson_prerequisites",
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("prerequisite_lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=50)),
        sa.Column("theory_opened", sa.Boolean()),
        sa.Column("theory_completed", sa.Boolean()),
        sa.Column("video_watched_percentage", sa.Float()),
        sa.Column("video_completed", sa.Boolean()),
        sa.Column("practical_submitted", sa.Boolean()),
        sa.Column("practical_passed", sa.Boolean()),
        sa.Column("quiz_passed", sa.Boolean()),
        sa.Column("best_quiz_score", sa.Float()),
        sa.Column("manual_override", sa.Boolean()),
        sa.Column("manual_override_by_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("override_reason", sa.Text()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson_progress"),
    )
    op.create_index("ix_lesson_progress_student_id", "lesson_progress", ["student_id"])
    op.create_index("ix_lesson_progress_lesson_id", "lesson_progress", ["lesson_id"])
    op.create_index("ix_lesson_progress_status", "lesson_progress", ["status"])

    op.create_table(
        "questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.String(length=36), sa.ForeignKey("modules.id")),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=50), nullable=False),
        sa.Column("difficulty", sa.String(length=50)),
        sa.Column("topic", sa.String(length=100)),
        sa.Column("tags", sa.JSON()),
        sa.Column("points", sa.Float()),
        sa.Column("explanation", sa.Text()),
        sa.Column("image_url", sa.Text()),
        sa.Column("created_by_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("status", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "quizzes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.String(length=36), sa.ForeignKey("modules.id")),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id")),
        sa.Column("passing_score", sa.Float(), nullable=False),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=False),
        sa.Column("allowed_attempts", sa.Integer(), nullable=False),
        sa.Column("shuffle_questions", sa.Boolean()),
        sa.Column("shuffle_options", sa.Boolean()),
        sa.Column("show_answers_mode", sa.String(length=50)),
        sa.Column("keep_score_mode", sa.String(length=50)),
        sa.Column("negative_marking", sa.Boolean()),
        sa.Column("availability_start", sa.DateTime()),
        sa.Column("availability_end", sa.DateTime()),
        sa.Column("is_required", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.String(length=36), sa.ForeignKey("courses.id")),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50)),
        sa.Column("assigned_instructor_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "video_progress",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_asset_id", sa.String(length=36), sa.ForeignKey("video_assets.id"), nullable=False),
        sa.Column("first_watched_at", sa.DateTime()),
        sa.Column("last_watched_at", sa.DateTime()),
        sa.Column("last_playback_position", sa.Float()),
        sa.Column("total_watched_seconds", sa.Float()),
        sa.Column("completion_percentage", sa.Float()),
        sa.Column("session_count", sa.Integer()),
        sa.Column("is_completed", sa.Boolean()),
        sa.Column("completed_at", sa.DateTime()),
        sa.UniqueConstraint("student_id", "lesson_id", "video_asset_id", name="uq_student_video_progress"),
    )

    op.create_table(
        "assignment_submissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assignment_id", sa.String(length=36), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submission_text", sa.Text()),
        sa.Column("github_url", sa.Text()),
        sa.Column("file_key", sa.String(length=500)),
        sa.Column("status", sa.String(length=50)),
        sa.Column("score", sa.Float()),
        sa.Column("instructor_feedback", sa.Text()),
        sa.Column("graded_by_id", sa.String(length=36), sa.ForeignKey("users.id")),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("graded_at", sa.DateTime()),
    )

    op.create_table(
        "code_drafts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id")),
        sa.Column("problem_id", sa.String(length=36), sa.ForeignKey("coding_problems.id")),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("student_id", "lesson_id", "problem_id", "language", name="uq_student_draft"),
    )

    op.create_table(
        "code_submissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("problem_id", sa.String(length=36), sa.ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(length=36), sa.ForeignKey("lessons.id")),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50)),
        sa.Column("score", sa.Float()),
        sa.Column("execution_time_seconds", sa.Float()),
        sa.Column("memory_used_kb", sa.Integer()),
        sa.Column("passed_test_cases", sa.Integer()),
        sa.Column("total_test_cases", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_code_submissions_student_id", "code_submissions", ["student_id"])
    op.create_index("ix_code_submissions_status", "code_submissions", ["status"])
    op.create_index("ix_code_submissions_lesson_id", "code_submissions", ["lesson_id"])
    op.create_index("ix_code_submissions_problem_id", "code_submissions", ["problem_id"])

    op.create_table(
        "coding_problem_languages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("problem_id", sa.String(length=36), sa.ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("starter_code", sa.Text(), nullable=False),
        sa.Column("solution_code", sa.Text()),
    )

    op.create_table(
        "question_options",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("order", sa.Integer()),
        sa.Column("match_pair", sa.Text()),
    )

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("quiz_id", sa.String(length=36), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50)),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime()),
        sa.Column("submitted_at", sa.DateTime()),
        sa.Column("score", sa.Float()),
        sa.Column("percentage", sa.Float()),
        sa.Column("passed", sa.Boolean()),
        sa.Column("questions_snapshot", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_quiz_attempts_quiz_id", "quiz_attempts", ["quiz_id"])
    op.create_index("ix_quiz_attempts_student_id", "quiz_attempts", ["student_id"])
    op.create_index("ix_quiz_attempts_status", "quiz_attempts", ["status"])

    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("quiz_id", sa.String(length=36), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order", sa.Integer()),
        sa.Column("points_override", sa.Float()),
    )

    op.create_table(
        "support_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("ticket_id", sa.String(length=36), sa.ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("attachment_url", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "test_cases",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("problem_id", sa.String(length=36), sa.ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input_data", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_public", sa.Boolean()),
        sa.Column("order", sa.Integer()),
        sa.Column("explanation", sa.Text()),
    )

    op.create_table(
        "quiz_attempt_questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attempt_id", sa.String(length=36), sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("question_snapshot", sa.JSON(), nullable=False),
        sa.Column("points_awarded", sa.Float()),
        sa.Column("is_correct", sa.Boolean()),
        sa.Column("feedback", sa.Text()),
    )

    op.create_table(
        "submission_test_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("submission_id", sa.String(length=36), sa.ForeignKey("code_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_case_id", sa.String(length=36), sa.ForeignKey("test_cases.id"), nullable=False),
        sa.Column("is_passed", sa.Boolean()),
        sa.Column("status", sa.String(length=50)),
        sa.Column("stdout", sa.Text()),
        sa.Column("stderr", sa.Text()),
        sa.Column("execution_time_seconds", sa.Float()),
        sa.Column("memory_used_kb", sa.Integer()),
    )

    op.create_table(
        "student_answers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attempt_question_id", sa.String(length=36), sa.ForeignKey("quiz_attempt_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("selected_option_ids", sa.JSON()),
        sa.Column("text_answer", sa.Text()),
        sa.Column("array_answer", sa.JSON()),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    for table_name in TABLE_DROP_ORDER:
        op.drop_table(table_name)
