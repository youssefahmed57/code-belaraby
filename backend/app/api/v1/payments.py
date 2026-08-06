import os
import uuid
import hashlib
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
from app.services.storage_service import StorageService, generate_signed_receipt_token, verify_signed_receipt_token

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
    import hashlib

    # Validate receipt file extension and MIME type
    filename = file.filename.lower() if file.filename else "receipt.png"
    ext = os.path.splitext(filename)[1]
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(
            status_code=400,
            detail="نوع الملف غير مسموح به. يرجى رفع صورة بصيغة JPG أو PNG أو WebP فقط."
        )

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="حجم الإيصال يتجاوز الحد الأقصى المسموح به (5 ميجابايت)."
        )

    # Validate Magic Bytes
    is_jpeg = contents[:3] == b"\xff\xd8\xff"
    is_png = contents[:8] == b"\x89PNG\r\n\x1a\n"
    is_webp = contents[:4] == b"RIFF" and contents[8:12] == b"WEBP"

    if not (is_jpeg or is_png or is_webp):
        raise HTTPException(
            status_code=400,
            detail="محتوى الملف غير صالح ولا يطابق صيغ الصور المسموح بها (Magic Bytes Mismatch)."
        )

    # Compute SHA-256 hash for duplicate receipt detection
    r_hash = hashlib.sha256(contents).hexdigest()
    stmt_dup = select(Payment).where(
        Payment.receipt_hash == r_hash,
        Payment.status.in_(["pending_review", "approved"])
    )
    res_dup = await db.execute(stmt_dup)
    if res_dup.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="عفواً، تم استخدام صورة هذا الإيصال سابقاً في طلب آخر. يرجى التأكد من رفع الإيصال الصحيح."
        )

    # Upload to Supabase Storage (or local storage fallback)
    file_key = f"receipts/{uuid.uuid4().hex}{ext}"
    content_type = file.content_type if file.content_type else "image/png"
    await StorageService.upload_file(contents, file_key, content_type)

    payment = await submit_payment_receipt(
        db=db,
        payment_id=payment_id,
        student_id=current_user.id,
        receipt_file_key=file_key,
        sender_identifier=sender_identifier,
        amount_submitted=amount_submitted,
        student_note=student_note
    )

    # Save hash
    payment.receipt_hash = r_hash
    await db.commit()
    await db.refresh(payment)

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

@router.post("/admin/generate-preview-url")
async def generate_preview_url(
    file_key: str,
    admin_user: User = Depends(require_roles(["admin", "super_admin"]))
):
    preview_url = await StorageService.generate_signed_url(file_key, expires_in_seconds=300)
    token = generate_signed_receipt_token(file_key, expires_in_seconds=300)
    return {
        "token": token,
        "preview_url": preview_url,
        "expires_in_seconds": 300
    }

@router.get("/preview")
async def preview_signed_receipt(token: str):
    from fastapi.responses import Response
    file_key = verify_signed_receipt_token(token)
    file_bytes = await StorageService.get_file_bytes(file_key)
    return Response(content=file_bytes, media_type="image/png", headers={"Cache-Control": "no-store, private"})

