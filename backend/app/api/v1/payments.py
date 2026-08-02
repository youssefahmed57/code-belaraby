import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.db.models import Payment, User, Course
from app.schemas.all_schemas import (
    CreatePaymentRequest, SubmitReceiptRequest, AdminReviewPaymentRequest, PaymentResponse
)
from app.services.payment_service import (
    create_payment_order, submit_payment_receipt, review_payment_admin
)
from app.api.deps import get_current_user, require_roles
from app.core.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/order", response_model=PaymentResponse)
async def request_payment(
    req: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    payment = await create_payment_order(
        db=db,
        student_id=current_user.id,
        course_id=req.course_id,
        payment_method=req.payment_method
    )
    return PaymentResponse.model_validate(payment)

@router.post("/upload-receipt", response_model=PaymentResponse)
async def upload_receipt(
    payment_id: str = Form(...),
    sender_identifier: str = Form(...),
    amount_submitted: float = Form(...),
    student_note: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate receipt file extension and MIME type
    filename = file.filename.lower() if file.filename else "receipt.png"
    ext = os.path.splitext(filename)[1]
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        raise HTTPException(
            status_code=400,
            detail="نوع الملف غير مسموح به. يرجى رفع صورة بصيغة JPG أو PNG أو ملف PDF."
        )

    # Save to local upload storage
    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    file_key = f"receipts/{uuid.uuid4().hex}{ext}"
    full_path = os.path.join(settings.STORAGE_LOCAL_DIR, file_key)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    contents = await file.read()
    with open(full_path, "wb") as f:
        f.write(contents)

    payment = await submit_payment_receipt(
        db=db,
        payment_id=payment_id,
        student_id=current_user.id,
        receipt_file_key=file_key,
        sender_identifier=sender_identifier,
        amount_submitted=amount_submitted,
        student_note=student_note
    )
    return PaymentResponse.model_validate(payment)

@router.get("/my-payments", response_model=List[PaymentResponse])
async def list_my_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Payment).where(Payment.student_id == current_user.id).order_by(Payment.created_at.desc())
    res = await db.execute(stmt)
    payments = res.scalars().all()
    return [PaymentResponse.model_validate(p) for p in payments]

@router.get("/admin/list", response_model=List[PaymentResponse])
async def admin_list_payments(
    status_filter: Optional[str] = None,
    admin_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Payment)
    if status_filter:
        stmt = stmt.where(Payment.status == status_filter)
    stmt = stmt.order_by(Payment.created_at.desc())

    res = await db.execute(stmt)
    payments = res.scalars().all()
    return [PaymentResponse.model_validate(p) for p in payments]

@router.post("/admin/review", response_model=PaymentResponse)
async def admin_review_payment(
    req: AdminReviewPaymentRequest,
    admin_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    payment = await review_payment_admin(
        db=db,
        payment_id=req.payment_id,
        reviewer_id=admin_user.id,
        action=req.action,
        review_note=req.review_note,
        rejection_reason=req.rejection_reason
    )
    return PaymentResponse.model_validate(payment)
