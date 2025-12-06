import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from backend.models.database import get_db, Payment, PaymentItem
from backend.services.payment_validator import PaymentValidator
from backend.services.qris_validator import QRISValidator
from pydantic import BaseModel

router = APIRouter()
validator = PaymentValidator()
qris_validator = QRISValidator()

class PaymentVerificationRequest(BaseModel):
    payment_id: int
    notification_id: int

class PaymentResponse(BaseModel):
    id: int
    amount: float
    reference_number: Optional[str]
    is_verified: bool
    payment_date: datetime
    ocr_confidence: Optional[float]
    
    class Config:
        from_attributes = True

@router.post("/validate-screenshot")
async def validate_payment_screenshot(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload payment screenshot and automatically validate QRIS payment
    Returns automatic validation result without human intervention
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded image
    upload_dir = "uploads/payment_screenshots"
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(upload_dir, f"{timestamp}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Automatic QRIS validation
    try:
        validation_result = qris_validator.validate_qris_payment(file_path)
        
        # Create payment record with automatic validation
        payment = Payment(
            amount=validation_result.get("amount", 0),
            ocr_amount=validation_result.get("amount"),
            ocr_date=validation_result.get("timestamp"),
            ocr_reference=validation_result.get("reference"),
            ocr_confidence=validation_result.get("ocr_confidence", 0),
            screenshot_path=file_path,
            payment_date=datetime.now(),
            reference_number=validation_result.get("reference", f"REF_{timestamp}"),
            # Automatically mark as verified if validation passes
            is_verified=validation_result.get("is_valid", False),
            bank_name=validation_result.get("bank", "Unknown"),
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return {
            "status": "success",
            "message": "Payment automatically validated",
            "payment_id": payment.id,
            "is_valid": validation_result.get("is_valid", False),
            "validation_confidence": validation_result.get("confidence", 0),
            "extracted_data": {
                "amount": validation_result.get("amount"),
                "timestamp": validation_result.get("timestamp"),
                "payment_method": validation_result.get("payment_method"),
                "bank": validation_result.get("bank"),
                "reference": validation_result.get("reference"),
            },
            "validation_details": validation_result.get("validation_details", {}),
            "auto_verified": validation_result.get("is_valid", False),
            "next_step": "Waiting for bank notification" if not validation_result.get("is_valid") else "Payment valid - Ready for processing"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment validation failed: {str(e)}")


@router.get("/pending", response_model=List[PaymentResponse])
async def get_pending_payments(db: Session = Depends(get_db)):
    """
    Get all payments waiting for verification
    """
    payments = db.query(Payment).filter(Payment.is_verified == False).all()
    return payments

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """
    Get payment details by ID
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.post("/verify")
async def verify_payment(
    request: PaymentVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Match payment screenshot with bank notification
    """
    is_match, confidence = validator.match_payment_with_notification(
        db, request.payment_id, request.notification_id
    )
    
    if is_match:
        payment = db.query(Payment).filter(Payment.id == request.payment_id).first()
        payment.is_verified = True
        payment.verified_at = datetime.utcnow()
        payment.notification_id = request.notification_id
        db.commit()
        
        return {
            "status": "verified",
            "message": "✅ Payment verified successfully!",
            "confidence": confidence,
            "payment_id": request.payment_id
        }
    else:
        return {
            "status": "failed",
            "message": "❌ Payment verification failed. Amount or time mismatch.",
            "confidence": confidence
        }

@router.get("/stats/today")
async def get_today_stats(db: Session = Depends(get_db)):
    """
    Get today's payment statistics
    """
    from sqlalchemy import func
    from datetime import date
    
    today = date.today()
    
    total_amount = db.query(func.sum(Payment.amount)).filter(
        func.date(Payment.payment_date) == today,
        Payment.is_verified == True
    ).scalar() or 0
    
    total_count = db.query(func.count(Payment.id)).filter(
        func.date(Payment.payment_date) == today,
        Payment.is_verified == True
    ).scalar() or 0
    
    pending_count = db.query(func.count(Payment.id)).filter(
        Payment.is_verified == False
    ).scalar() or 0
    
    return {
        "date": today.isoformat(),
        "total_revenue": total_amount,
        "verified_payments": total_count,
        "pending_payments": pending_count
    }
