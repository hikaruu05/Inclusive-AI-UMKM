import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from backend.models.database import get_db, BankNotification
from backend.services.notification_parser import NotificationParser

router = APIRouter()
parser = NotificationParser()

class NotificationCreate(BaseModel):
    source: str  # "BCA", "Mandiri", "GoPay", "Dana", etc.
    raw_text: str

class NotificationResponse(BaseModel):
    id: int
    source: str
    amount: float
    transaction_date: datetime
    reference_number: str
    sender_name: str
    is_matched: bool
    
    class Config:
        from_attributes = True

@router.post("/submit")
async def submit_bank_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """
    Submit bank notification (SMS/push notification text)
    This would typically come from the Android app or manual merchant input
    """
    try:
        # Parse notification text
        parsed_data = parser.parse_notification(
            notification.raw_text,
            notification.source
        )
        
        # Create notification record
        new_notification = BankNotification(
            source=notification.source,
            raw_text=notification.raw_text,
            amount=parsed_data.get("amount"),
            transaction_date=parsed_data.get("date", datetime.utcnow()),
            reference_number=parsed_data.get("reference"),
            sender_name=parsed_data.get("sender")
        )
        
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)
        
        # Try to auto-match with pending payments
        from services.payment_validator import PaymentValidator
        validator = PaymentValidator()
        match_result = validator.auto_match_notification(db, new_notification.id)
        
        if match_result["matched"]:
            return {
                "status": "success",
                "message": "✅ Notification received and auto-matched!",
                "notification_id": new_notification.id,
                "payment_id": match_result["payment_id"],
                "auto_matched": True
            }
        else:
            return {
                "status": "success",
                "message": "Notification received. Waiting for payment screenshot.",
                "notification_id": new_notification.id,
                "parsed_data": parsed_data,
                "auto_matched": False
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process notification: {str(e)}")

@router.get("/pending")
async def get_pending_notifications(db: Session = Depends(get_db)):
    """
    Get all notifications that haven't been matched yet
    """
    notifications = db.query(BankNotification).filter(
        BankNotification.is_matched == False
    ).all()
    
    return {
        "count": len(notifications),
        "notifications": [
            {
                "id": n.id,
                "source": n.source,
                "amount": n.amount,
                "date": n.transaction_date.isoformat() if n.transaction_date else None,
                "reference": n.reference_number,
                "received_at": n.received_at.isoformat()
            }
            for n in notifications
        ]
    }

@router.get("/{notification_id}")
async def get_notification(notification_id: int, db: Session = Depends(get_db)):
    """
    Get specific notification details
    """
    notification = db.query(BankNotification).filter(
        BankNotification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {
        "id": notification.id,
        "source": notification.source,
        "raw_text": notification.raw_text,
        "parsed": {
            "amount": notification.amount,
            "date": notification.transaction_date.isoformat() if notification.transaction_date else None,
            "reference": notification.reference_number,
            "sender": notification.sender_name
        },
        "is_matched": notification.is_matched,
        "matched_at": notification.matched_at.isoformat() if notification.matched_at else None
    }

@router.post("/test-parse")
async def test_notification_parsing(notification: NotificationCreate):
    """
    Test notification parsing without saving to database
    Useful for debugging and testing different bank formats
    """
    try:
        parsed_data = parser.parse_notification(
            notification.raw_text,
            notification.source
        )
        
        return {
            "status": "success",
            "source": notification.source,
            "raw_text": notification.raw_text,
            "parsed_data": parsed_data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
