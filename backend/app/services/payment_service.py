import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.db.models import Payment, PaymentEvent, Enrolment, Course, User, AuditLog, Notification, LessonProgress, Lesson, Module

def generate_payment_reference() -> str:
    # Format: PAY-YYYYMMDD-XXXX
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_str = str(uuid.uuid4().hex[:6]).upper()
    return f"PAY-{date_str}-{random_str}"

async def create_payment_order(
    db: AsyncSession,
    student_id: str,
    course_id: str,
    payment_method: str
) -> Payment:
    # Check course
    stmt_c = select(Course).where(Course.id == course_id)
    res_c = await db.execute(stmt_c)
    course = res_c.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="الكورس غير موجود.")

    ref_code = generate_payment_reference()
    payment = Payment(
        reference_code=ref_code,
        student_id=student_id,
        course_id=course_id,
        amount_expected=course.discount_price if course.discount_price else course.price,
        payment_method=payment_method,
        status="awaiting_receipt"
    )
    db.add(payment)
    await db.flush()

    db.add(PaymentEvent(
        payment_id=payment.id,
        previous_status=None,
        new_status="awaiting_receipt",
        actor_id=student_id,
        comment="تم إنشاء طلب الدفع وفي انتظار رفع الصورة"
    ))

    await db.commit()
    await db.refresh(payment)
    return payment

async def submit_payment_receipt(
    db: AsyncSession,
    payment_id: str,
    student_id: str,
    receipt_file_key: str,
    sender_identifier: str,
    amount_submitted: float,
    student_note: Optional[str] = None
) -> Payment:
    stmt = select(Payment).where(Payment.id == payment_id, Payment.student_id == student_id)
    res = await db.execute(stmt)
    payment = res.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="طلب الدفع غير موجود.")

    prev_status = payment.status
    payment.receipt_file_key = receipt_file_key
    payment.sender_identifier = sender_identifier
    payment.amount_submitted = amount_submitted
    payment.student_note = student_note
    payment.status = "pending_review"
    payment.submitted_at = datetime.utcnow()

    db.add(PaymentEvent(
        payment_id=payment.id,
        previous_status=prev_status,
        new_status="pending_review",
        actor_id=student_id,
        comment="تم رفع إيصال التحويل وبانتظار مراجعة الإدارة"
    ))

    # Notification for student
    db.add(Notification(
        user_id=student_id,
        title="تم استلام إيصال الدفع",
        message=f"تم إرسال إيصال طلب الدفع {payment.reference_code} وجاري مراجعته من قبل الإدارة.",
        type="payment"
    ))

    await db.commit()
    await db.refresh(payment)
    return payment

async def review_payment_admin(
    db: AsyncSession,
    payment_id: str,
    reviewer_id: str,
    action: str, # approve, reject, request_info
    review_note: Optional[str] = None,
    rejection_reason: Optional[str] = None
) -> Payment:
    stmt = select(Payment).where(Payment.id == payment_id)
    res = await db.execute(stmt)
    payment = res.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="طلب الدفع غير موجود.")

    prev_status = payment.status
    payment.reviewer_id = reviewer_id
    payment.review_note = review_note
    payment.reviewed_at = datetime.utcnow()

    if action == "approve":
        payment.status = "approved"
        
        # Transactionally create or activate enrolment
        stmt_enrol = select(Enrolment).where(
            Enrolment.student_id == payment.student_id,
            Enrolment.course_id == payment.course_id
        )
        res_enrol = await db.execute(stmt_enrol)
        enrolment = res_enrol.scalar_one_or_none()

        course_stmt = select(Course).where(Course.id == payment.course_id)
        res_c = await db.execute(course_stmt)
        course = res_c.scalar_one_or_none()
        access_days = course.access_duration_days if course else 365

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
                approved_by_id=reviewer_id
            )
            db.add(enrolment)

        # Unlock Lesson 1 automatically
        stmt_first_lesson = select(Lesson).join(Module).where(
            Module.course_id == payment.course_id,
            Module.order == 1,
            Lesson.order == 1
        )
        res_l1 = await db.execute(stmt_first_lesson)
        l1 = res_l1.scalar_one_or_none()
        if l1:
            lp_stmt = select(LessonProgress).where(
                LessonProgress.student_id == payment.student_id,
                LessonProgress.lesson_id == l1.id
            )
            res_lp = await db.execute(lp_stmt)
            lp = res_lp.scalar_one_or_none()
            if not lp:
                db.add(LessonProgress(
                    student_id=payment.student_id,
                    lesson_id=l1.id,
                    status="available"
                ))

        # Notification for student
        db.add(Notification(
            user_id=payment.student_id,
            title="تم قبول طلب الدفع!",
            message=f"تهانينا! تم تفعيل اشتراكك في كورس ({course.title if course else ''}) بنجاح.",
            type="payment"
        ))

    elif action == "reject":
        payment.status = "rejected"
        payment.rejection_reason = rejection_reason or "لم يتم التأكد من صحة التحويل."
        
        db.add(Notification(
            user_id=payment.student_id,
            title="رفض طلب الدفع",
            message=f"عذراً، تعذر قبول طلب الدفع {payment.reference_code}. السبب: {payment.rejection_reason}",
            type="payment"
        ))

    elif action == "request_info":
        payment.status = "more_info_required"
        payment.review_note = review_note or "يرجى توضيح تفاصيل إضافية عن التحويل."

    db.add(PaymentEvent(
        payment_id=payment.id,
        previous_status=prev_status,
        new_status=payment.status,
        actor_id=reviewer_id,
        comment=f"تم تغيير حالة طلب الدفع إلى {payment.status}. ملاحظة: {review_note or ''}"
    ))

    db.add(AuditLog(
        user_id=reviewer_id,
        action=f"PAYMENT_{action.upper()}",
        entity_type="payments",
        entity_id=payment.id,
        details={"status": payment.status, "student_id": payment.student_id}
    ))

    await db.commit()
    await db.refresh(payment)
    return payment
