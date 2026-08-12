import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AuditLog,
    Course,
    Enrolment,
    Lesson,
    LessonProgress,
    Module,
    Notification,
    Payment,
    PaymentEvent,
)


PAYMENT_TRANSITIONS = {
    "draft": {"awaiting_receipt", "cancelled"},
    "awaiting_receipt": {"pending_review", "cancelled"},
    "pending_review": {"approved", "rejected", "more_info_required"},
    "more_info_required": {"pending_review", "cancelled"},
    "approved": set(),
    "rejected": {"pending_review"},
    "cancelled": set(),
    "refunded": set(),
}
REUSABLE_PAYMENT_STATUSES = {"draft", "awaiting_receipt", "more_info_required"}


def validate_payment_transition(current_status: str, new_status: str) -> None:
    allowed = PAYMENT_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"لا يمكن تغيير حالة الدفع من '{current_status}' إلى '{new_status}'.",
        )


def generate_payment_reference() -> str:
    return f"PAY-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


async def _first_published_lesson(db: AsyncSession, course_id: str) -> Optional[Lesson]:
    first_module = await db.scalar(
        select(Module)
        .where(Module.course_id == course_id, Module.status == "published")
        .order_by(Module.order)
        .limit(1)
    )
    if not first_module:
        return None
    return await db.scalar(
        select(Lesson)
        .where(Lesson.module_id == first_module.id, Lesson.publishing_status == "published")
        .order_by(Lesson.order)
        .limit(1)
    )


async def create_payment_order(
    db: AsyncSession,
    student_id: str,
    course_id: str,
    payment_method: str,
) -> Payment:
    course = await db.scalar(select(Course).where(Course.id == course_id, Course.status == "published"))
    if not course:
        raise HTTPException(status_code=404, detail="الكورس غير موجود.")

    latest_payment = await db.scalar(
        select(Payment)
        .where(Payment.student_id == student_id, Payment.course_id == course_id)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    if latest_payment:
        if latest_payment.status in REUSABLE_PAYMENT_STATUSES:
            return latest_payment
        if latest_payment.status == "pending_review":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="يوجد بالفعل طلب دفع لهذا الكورس قيد المراجعة. يمكنك انتظار نتيجة المراجعة الحالية.",
            )
        if latest_payment.status == "approved":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="تم اعتماد طلب الدفع لهذا الكورس بالفعل ولا يمكن إنشاء طلب جديد حالياً.",
            )

    payment = Payment(
        reference_code=generate_payment_reference(),
        student_id=student_id,
        course_id=course_id,
        amount_expected=course.discount_price if course.discount_price is not None else course.price,
        payment_method=payment_method,
        status="awaiting_receipt",
    )
    db.add(payment)
    await db.flush()

    db.add(
        PaymentEvent(
            payment_id=payment.id,
            previous_status=None,
            new_status="awaiting_receipt",
            actor_id=student_id,
            comment="تم إنشاء طلب الدفع وفي انتظار رفع الإيصال.",
        )
    )

    await db.commit()
    await db.refresh(payment)
    return payment


async def submit_payment_receipt(
    db: AsyncSession,
    payment_id: str,
    student_id: str,
    receipt_file_key: str,
    receipt_hash: str,
    sender_identifier: str,
    amount_submitted: Decimal,
    student_note: Optional[str] = None,
) -> Payment:
    payment = await db.scalar(
        select(Payment)
        .where(Payment.id == payment_id, Payment.student_id == student_id)
        .with_for_update()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="طلب الدفع غير موجود.")

    validate_payment_transition(payment.status, "pending_review")
    previous_status = payment.status
    payment.receipt_file_key = receipt_file_key
    payment.receipt_hash = receipt_hash
    payment.sender_identifier = sender_identifier
    payment.amount_submitted = amount_submitted
    payment.student_note = student_note
    payment.status = "pending_review"
    payment.submitted_at = datetime.utcnow()

    db.add(
        PaymentEvent(
            payment_id=payment.id,
            previous_status=previous_status,
            new_status="pending_review",
            actor_id=student_id,
            comment="تم رفع إيصال التحويل وبانتظار المراجعة.",
        )
    )
    db.add(
        Notification(
            user_id=student_id,
            title="تم استلام إيصال الدفع",
            message=f"تم إرسال إيصال طلب الدفع {payment.reference_code} وجارٍ مراجعته من قبل الإدارة.",
            type="payment",
        )
    )

    await db.commit()
    await db.refresh(payment)
    return payment


async def review_payment_admin(
    db: AsyncSession,
    payment_id: str,
    reviewer_id: str,
    action: str,
    review_note: Optional[str] = None,
    rejection_reason: Optional[str] = None,
) -> Payment:
    payment = await db.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if not payment:
        raise HTTPException(status_code=404, detail="طلب الدفع غير موجود.")

    if payment.status == "approved" and action == "approve":
        return payment
    if payment.status == "rejected" and action == "reject":
        return payment

    target_status = {"approve": "approved", "reject": "rejected", "request_info": "more_info_required"}.get(action)
    if not target_status:
        raise HTTPException(status_code=400, detail="إجراء مراجعة غير معروف.")
    validate_payment_transition(payment.status, target_status)

    previous_status = payment.status
    payment.reviewer_id = reviewer_id
    payment.review_note = review_note
    payment.reviewed_at = datetime.utcnow()

    if action == "approve":
        if payment.amount_submitted is None:
            raise HTTPException(status_code=400, detail="لا يمكن اعتماد الطلب قبل تسجيل المبلغ المحول من الطالب.")
        if Decimal(payment.amount_submitted) < Decimal(payment.amount_expected):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="لا يمكن اعتماد هذا الطلب لأن المبلغ المحول أقل من المبلغ المطلوب للكورس.",
            )

        payment.status = "approved"
        course = await db.scalar(select(Course).where(Course.id == payment.course_id))
        access_days = course.access_duration_days if course else 365

        enrolment = await db.scalar(
            select(Enrolment)
            .where(Enrolment.student_id == payment.student_id, Enrolment.course_id == payment.course_id)
            .with_for_update()
        )
        if enrolment:
            enrolment.status = "active"
            enrolment.access_start = datetime.utcnow()
            enrolment.access_expiry = datetime.utcnow() + timedelta(days=access_days)
            enrolment.payment_id = payment.id
            enrolment.approved_by_id = reviewer_id
        else:
            enrolment = Enrolment(
                student_id=payment.student_id,
                course_id=payment.course_id,
                status="active",
                access_start=datetime.utcnow(),
                access_expiry=datetime.utcnow() + timedelta(days=access_days),
                payment_id=payment.id,
                source="manual_payment",
                approved_by_id=reviewer_id,
            )
            db.add(enrolment)
            try:
                await db.flush()
            except IntegrityError as exc:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="تعذر اعتماد الدفع بسبب تعارض متزامن في حالة الاشتراك.",
                ) from exc

        first_lesson = await _first_published_lesson(db, payment.course_id)
        if first_lesson:
            lesson_progress = await db.scalar(
                select(LessonProgress).where(
                    LessonProgress.student_id == payment.student_id,
                    LessonProgress.lesson_id == first_lesson.id,
                )
            )
            if not lesson_progress:
                db.add(LessonProgress(student_id=payment.student_id, lesson_id=first_lesson.id, status="available"))
            elif lesson_progress.status == "locked":
                lesson_progress.status = "available"

        db.add(
            Notification(
                user_id=payment.student_id,
                title="تم قبول طلب الدفع",
                message=f"تم تفعيل اشتراكك في كورس ({course.title if course else ''}) بنجاح.",
                type="payment",
            )
        )
    elif action == "reject":
        payment.status = "rejected"
        payment.rejection_reason = rejection_reason or "تعذر التحقق من صحة التحويل."
        db.add(
            Notification(
                user_id=payment.student_id,
                title="تم رفض طلب الدفع",
                message=f"تم رفض طلب الدفع {payment.reference_code}. السبب: {payment.rejection_reason}",
                type="payment",
            )
        )
    else:
        payment.status = "more_info_required"
        payment.review_note = review_note or "يرجى تزويدنا بتفاصيل إضافية عن التحويل."

    db.add(
        PaymentEvent(
            payment_id=payment.id,
            previous_status=previous_status,
            new_status=payment.status,
            actor_id=reviewer_id,
            comment=review_note or "",
        )
    )
    db.add(
        AuditLog(
            user_id=reviewer_id,
            action=f"PAYMENT_{action.upper()}",
            entity_type="payments",
            entity_id=payment.id,
            details={"status": payment.status, "student_id": payment.student_id},
        )
    )

    await db.commit()
    await db.refresh(payment)
    return payment
