import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.db.models import User, Payment, Enrolment, Course, LessonProgress, AuditLog
from app.api.deps import require_roles, get_current_user

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/metrics")
async def get_admin_metrics(
    admin_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime, timedelta
    from app.db.models import UserRole, Role

    # Total students (users with 'student' role, not all active users)
    stmt_student_role = select(func.count(UserRole.id)).join(
        Role, UserRole.role_id == Role.id
    ).join(
        User, UserRole.user_id == User.id
    ).where(Role.name == "student", User.status == "active")
    res_students = await db.execute(stmt_student_role)
    total_students = res_students.scalar() or 0

    # Active enrolments
    res_enrol = await db.execute(select(func.count(Enrolment.id)).where(Enrolment.status == "active"))
    active_enrolments = res_enrol.scalar() or 0

    # Pending payments
    res_pay = await db.execute(select(func.count(Payment.id)).where(Payment.status == "pending_review"))
    pending_payments = res_pay.scalar() or 0

    # Approved revenue
    res_rev = await db.execute(select(func.sum(Payment.amount_submitted)).where(Payment.status == "approved"))
    approved_revenue = res_rev.scalar() or 0.0

    # Today's registrations (real data)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    res_today = await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    today_registrations = res_today.scalar() or 0

    # Lesson completion rate (real data)
    res_total_lp = await db.execute(
        select(func.count(LessonProgress.id)).where(LessonProgress.status.in_(["in_progress", "completed"]))
    )
    total_lp = res_total_lp.scalar() or 0
    res_completed_lp = await db.execute(
        select(func.count(LessonProgress.id)).where(LessonProgress.status == "completed")
    )
    completed_lp = res_completed_lp.scalar() or 0
    lesson_completion_rate = round((completed_lp / total_lp * 100.0) if total_lp > 0 else 0.0, 1)

    return {
        "total_students": total_students,
        "active_enrolments": active_enrolments,
        "pending_payments": pending_payments,
        "approved_revenue": round(float(approved_revenue), 2),
        "today_registrations": today_registrations,
        "lesson_completion_rate": lesson_completion_rate
    }

@router.get("/students")
async def list_students(
    search: Optional[str] = None,
    admin_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).order_by(User.created_at.desc())
    if search:
        safe_search = search.replace("%", "\\%").replace("_", "\\_")
        stmt = stmt.where((User.arabic_name.ilike(f"%{safe_search}%")) | (User.phone_number.ilike(f"%{safe_search}%")))

    res = await db.execute(stmt)
    users = res.scalars().all()

    return [
        {
            "id": u.id,
            "arabic_name": u.arabic_name,
            "phone_number": u.phone_number,
            "email": u.email,
            "grade_level": u.grade_level,
            "status": u.status,
            "created_at": u.created_at
        } for u in users
    ]

@router.get("/export-csv")
async def export_students_csv(
    admin_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).order_by(User.created_at.desc())
    res = await db.execute(stmt)
    users = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Phone", "Email", "Grade Level", "Status", "Created At"])

    for u in users:
        writer.writerow([u.id, u.arabic_name, u.phone_number, u.email or "", u.grade_level, u.status, u.created_at.strftime("%Y-%m-%d %H:%M")])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")), # UTF-8 BOM for Excel Arabic support
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_export.csv"}
    )
