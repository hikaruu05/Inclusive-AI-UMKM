import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import os

from backend.services.payment_ocr import PaymentOCR
from backend.models.database import Payment, BankNotification

class PaymentValidator:
    """
    Service to validate payment screenshots against bank notifications
    Acts as the "middleman" to prevent fraud and automate verification
    """
    
    def __init__(self):
        self.ocr = PaymentOCR()
        
        # Configuration from environment
        self.match_threshold = float(os.getenv("PAYMENT_MATCH_THRESHOLD", "0.95"))
        self.time_window_minutes = int(os.getenv("TIME_WINDOW_MINUTES", "10"))
    
    def extract_payment_info(self, image_path: str) -> Dict:
        """
        Extract payment information from screenshot using OCR
        """
        return self.ocr.extract_payment_info(image_path)
    
    def amounts_match(self, amount1: float, amount2: float, tolerance: float = 0.01) -> bool:
        """
        Check if two amounts match within tolerance
        Tolerance accounts for rounding differences
        """
        if not amount1 or not amount2:
            return False
        
        difference = abs(amount1 - amount2)
        return difference <= max(amount1, amount2) * tolerance
    
    def times_match(self, time1: datetime, time2: datetime) -> bool:
        """
        Check if two timestamps are within acceptable time window
        """
        if not time1 or not time2:
            return False
        
        time_diff = abs((time1 - time2).total_seconds() / 60)  # Convert to minutes
        return time_diff <= self.time_window_minutes
    
    def match_payment_with_notification(
        self,
        db: Session,
        payment_id: int,
        notification_id: int
    ) -> Tuple[bool, float]:
        """
        Match a payment screenshot with a bank notification
        Returns (is_match, confidence_score)
        """
        # Get payment and notification from database
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        notification = db.query(BankNotification).filter(BankNotification.id == notification_id).first()
        
        if not payment or not notification:
            return False, 0.0
        
        # Check amount match
        amount_match = self.amounts_match(payment.ocr_amount, notification.amount)
        
        # Check time match
        time_match = self.times_match(payment.ocr_date, notification.transaction_date)
        
        # Check reference if available
        reference_match = False
        if payment.ocr_reference and notification.reference_number:
            reference_match = payment.ocr_reference.lower() == notification.reference_number.lower()
        
        # Calculate confidence score
        confidence = 0.0
        
        if amount_match:
            confidence += 0.6  # Amount is most important
        
        if time_match:
            confidence += 0.3  # Time window is important
        
        if reference_match:
            confidence += 0.1  # Reference is bonus
        
        # Consider OCR confidence
        if payment.ocr_confidence:
            confidence *= payment.ocr_confidence
        
        # Match if confidence exceeds threshold
        is_match = confidence >= self.match_threshold
        
        return is_match, confidence
    
    def auto_match_notification(
        self,
        db: Session,
        notification_id: int
    ) -> Dict:
        """
        Try to automatically match a new notification with pending payments
        Returns dict with match status and payment_id if matched
        """
        notification = db.query(BankNotification).filter(
            BankNotification.id == notification_id
        ).first()
        
        if not notification:
            return {"matched": False, "reason": "Notification not found"}
        
        # Get all unverified payments within time window
        time_cutoff = datetime.utcnow() - timedelta(minutes=self.time_window_minutes)
        
        pending_payments = db.query(Payment).filter(
            Payment.is_verified == False,
            Payment.created_at >= time_cutoff
        ).all()
        
        if not pending_payments:
            return {"matched": False, "reason": "No pending payments in time window"}
        
        # Try to match with each pending payment
        best_match = None
        best_confidence = 0.0
        
        for payment in pending_payments:
            is_match, confidence = self.match_payment_with_notification(
                db, payment.id, notification_id
            )
            
            if is_match and confidence > best_confidence:
                best_match = payment
                best_confidence = confidence
        
        if best_match:
            # Mark both as matched
            best_match.is_verified = True
            best_match.verified_at = datetime.utcnow()
            best_match.notification_id = notification_id
            
            notification.is_matched = True
            notification.matched_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "matched": True,
                "payment_id": best_match.id,
                "confidence": best_confidence
            }
        
        return {
            "matched": False,
            "reason": f"No matching payment found. Checked {len(pending_payments)} pending payments."
        }
    
    def get_verification_summary(self, db: Session) -> Dict:
        """
        Get summary of verification statistics
        """
        total_payments = db.query(Payment).count()
        verified_payments = db.query(Payment).filter(Payment.is_verified == True).count()
        pending_payments = total_payments - verified_payments
        
        total_notifications = db.query(BankNotification).count()
        matched_notifications = db.query(BankNotification).filter(
            BankNotification.is_matched == True
        ).count()
        
        return {
            "payments": {
                "total": total_payments,
                "verified": verified_payments,
                "pending": pending_payments,
                "verification_rate": f"{(verified_payments/total_payments*100):.1f}%" if total_payments > 0 else "0%"
            },
            "notifications": {
                "total": total_notifications,
                "matched": matched_notifications,
                "unmatched": total_notifications - matched_notifications
            }
        }
