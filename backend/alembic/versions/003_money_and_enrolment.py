"""Production hardening: Float to Numeric money columns + enrolment unique constraint

Revision ID: 003_money_and_enrolment
Revises: 002_security_tables
Create Date: 2026-08-12 05:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '003_money_and_enrolment'
down_revision = '002_security_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    dialect = bind.dialect.name

    # --- 1. Convert money columns from Float to Numeric(12,2) ---
    money_columns = [
        ("courses", "price"),
        ("courses", "discount_price"),
        ("payments", "amount_expected"),
        ("payments", "amount_submitted"),
        ("coupons", "discount_value"),
        ("coupon_usages", "discount_amount"),
    ]

    for table_name, col_name in money_columns:
        if table_name in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns(table_name)]
            if col_name in cols:
                if dialect == "postgresql":
                    # PostgreSQL: safe ALTER with USING cast
                    op.execute(
                        f'ALTER TABLE "{table_name}" '
                        f'ALTER COLUMN "{col_name}" TYPE NUMERIC(12,2) '
                        f'USING "{col_name}"::NUMERIC(12,2)'
                    )
                elif dialect == "sqlite":
                    # SQLite doesn't support ALTER COLUMN TYPE.
                    # The ORM already defines Numeric; SQLite stores as TEXT/REAL
                    # which is functionally equivalent. No-op for SQLite.
                    pass

    # --- 2. Add UniqueConstraint on enrolments(student_id, course_id) ---
    if "enrolments" in inspector.get_table_names():
        existing_uqs = inspector.get_unique_constraints("enrolments")
        uq_names = [uq['name'] for uq in existing_uqs if uq.get('name')]
        if "uq_enrolment_student_course" not in uq_names:
            if dialect == "postgresql":
                op.create_unique_constraint(
                    "uq_enrolment_student_course",
                    "enrolments",
                    ["student_id", "course_id"]
                )
            elif dialect == "sqlite":
                # SQLite doesn't support ADD CONSTRAINT. Create index instead.
                existing_indexes = inspector.get_indexes("enrolments")
                idx_names = [idx['name'] for idx in existing_indexes if idx.get('name')]
                if "ix_enrolment_student_course_unique" not in idx_names:
                    op.create_index(
                        "ix_enrolment_student_course_unique",
                        "enrolments",
                        ["student_id", "course_id"],
                        unique=True
                    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    dialect = bind.dialect.name

    # Reverse unique constraint
    if "enrolments" in inspector.get_table_names():
        if dialect == "postgresql":
            existing_uqs = inspector.get_unique_constraints("enrolments")
            uq_names = [uq['name'] for uq in existing_uqs if uq.get('name')]
            if "uq_enrolment_student_course" in uq_names:
                op.drop_constraint("uq_enrolment_student_course", "enrolments", type_="unique")
        elif dialect == "sqlite":
            existing_indexes = inspector.get_indexes("enrolments")
            idx_names = [idx['name'] for idx in existing_indexes if idx.get('name')]
            if "ix_enrolment_student_course_unique" in idx_names:
                op.drop_index("ix_enrolment_student_course_unique", table_name="enrolments")

    # Reverse money columns (Numeric back to Float)
    money_columns = [
        ("courses", "price"),
        ("courses", "discount_price"),
        ("payments", "amount_expected"),
        ("payments", "amount_submitted"),
        ("coupons", "discount_value"),
        ("coupon_usages", "discount_amount"),
    ]
    for table_name, col_name in money_columns:
        if table_name in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns(table_name)]
            if col_name in cols:
                if dialect == "postgresql":
                    op.execute(
                        f'ALTER TABLE "{table_name}" '
                        f'ALTER COLUMN "{col_name}" TYPE DOUBLE PRECISION '
                        f'USING "{col_name}"::DOUBLE PRECISION'
                    )
