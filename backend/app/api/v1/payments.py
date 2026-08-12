import hashlib
import os
import uuid
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.db.models import Payment, User
from app.schemas.all_schemas import AdminReviewPaymentRequest, CreatePaymentRequest, PaymentResponse
from app.services.payment_service import create_payment_order, review_payment_admin, submit_payment_receipt
from app.services.storage_service import StorageService, generate_signed_receipt_token, verify_signed_receipt_token


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/order", response_model=PaymentResponse)
async def request_payment(
    req: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment = await create_payment_order(
        db=db,
        student_id=current_user.id,
        course_id=req.course_id,
        payment_method=req.payment_method,
    )
    return PaymentResponse.model_validate(payment)


@router.post("/upload-receipt", response_model=PaymentResponse)
async def upload_receipt(
    payment_id: str = Form(...),
    sender_identifier: str = Form(...),
    amount_submitted: str = Form(...),
    student_note: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filename = (file.filename or "receipt.png").lower()
    extension = os.path.splitext(filename)[1]
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(
            status_code=400,
            detail="نوع الملف غير مسموح به. يرجى رفع صورة بصيغة JPG أو PNG أو WebP فقط.",
        )

    payment = await db.scalar(select(Payment).where(Payment.id == payment_id))
    if not payment:
        raise HTTPException(status_code=404, detail="طلب الدفع غير موجود.")
    if payment.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="لا يمكنك رفع إيصال لطلب دفع لا يخصك.")
    if payment.status not in {"draft", "awaiting_receipt", "more_info_required"}:
        raise HTTPException(status_code=409, detail=f"لا يمكن رفع إيصال لطلب بحالة '{payment.status}'.")

    try:
        submitted_amount = Decimal(amount_submitted)
    except (InvalidOperation, TypeError):
        raise HTTPException(status_code=400, detail="قيمة المبلغ المحول غير صالحة.")
    if submitted_amount <= 0:
        raise HTTPException(status_code=400, detail="المبلغ المحول يجب أن يكون أكبر من صفر.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="حجم الإيصال يتجاوز الحد الأقصى المسموح به (5 ميجابايت).")

    is_jpeg = contents[:3] == b"\xff\xd8\xff"
    is_png = contents[:8] == b"\x89PNG\r\n\x1a\n"
    is_webp = contents[:4] == b"RIFF" and contents[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        raise HTTPException(status_code=400, detail="محتوى الملف غير صالح ولا يطابق صيغ الصور المسموح بها.")

    receipt_hash = hashlib.sha256(contents).hexdigest()
    duplicate_payment = await db.scalar(
        select(Payment).where(
            Payment.receipt_hash == receipt_hash,
            Payment.status.in_(["pending_review", "approved"]),
        )
    )
    if duplicate_payment:
        raise HTTPException(
            status_code=400,
            detail="تم استخدام صورة هذا الإيصال سابقاً في طلب آخر.",
        )

    file_key = f"receipts/{uuid.uuid4().hex}{extension}"
    uploaded_key: Optional[str] = None
    try:
        uploaded_key = await StorageService.upload_file(contents, file_key, file.content_type or "image/png")
        payment = await submit_payment_receipt(
            db=db,
            payment_id=payment_id,
            student_id=current_user.id,
            receipt_file_key=uploaded_key,
            receipt_hash=receipt_hash,
            sender_identifier=sender_identifier,
            amount_submitted=submitted_amount,
            student_note=student_note,
        )
    except Exception:
        if uploaded_key:
            try:
                await StorageService.delete_file(uploaded_key)
            except Exception:
                pass
        raise

    return PaymentResponse.model_validate(payment)


@router.get("/my-payments", response_model=List[PaymentResponse])
async def list_my_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payments = (
        await db.execute(
            select(Payment).where(Payment.student_id == current_user.id).order_by(Payment.created_at.desc())
        )
    ).scalars().all()
    return [PaymentResponse.model_validate(payment) for payment in payments]


@router.get("/admin/list", response_model=List[PaymentResponse])
async def admin_list_payments(
    status_filter: Optional[str] = None,
    admin_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db),
):
    statement = select(Payment)
    if status_filter:
        statement = statement.where(Payment.status == status_filter)
    payments = (await db.execute(statement.order_by(Payment.created_at.desc()))).scalars().all()
    return [PaymentResponse.model_validate(payment) for payment in payments]


@router.post("/admin/review", response_model=PaymentResponse)
async def admin_review_payment(
    req: AdminReviewPaymentRequest,
    admin_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db),
):
    payment = await review_payment_admin(
        db=db,
        payment_id=req.payment_id,
        reviewer_id=admin_user.id,
        action=req.action,
        review_note=req.review_note,
        rejection_reason=req.rejection_reason,
    )
    return PaymentResponse.model_validate(payment)


@router.post("/admin/generate-preview-url")
async def generate_preview_url(
    file_key: str,
    admin_user: User = Depends(require_roles(["admin", "super_admin"])),
):
    preview_url = await StorageService.generate_signed_url(file_key, expires_in_seconds=300)
    token = generate_signed_receipt_token(file_key, expires_in_seconds=300)
    return {
        "token": token,
        "preview_url": preview_url,
        "expires_in_seconds": 300,
    }


@router.get("/preview")
async def preview_signed_receipt(
    token: str,
    _admin_user: User = Depends(require_roles(["admin", "super_admin"])),
):
    file_key = verify_signed_receipt_token(token)
    file_bytes = await StorageService.get_file_bytes(file_key)
    return Response(
        content=file_bytes,
        media_type=StorageService.guess_media_type(file_key),
        headers={"Cache-Control": "no-store, private"},
    )
