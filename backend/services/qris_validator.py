import re
from typing import Dict, Optional, Tuple
from datetime import datetime
import cv2
import numpy as np
from backend.services.payment_ocr import PaymentOCR

class QRISValidator:
    """Automatic QRIS payment validation service"""
    
    # QRIS-specific patterns and rules
    QRIS_KEYWORDS = ['qris', 'qr', 'gopay', 'ovo', 'dana', 'linkaja', 'shopeepay', 'mandiri', 'bca', 'bni', 'bri']
    REQUIRED_FIELDS = ['amount', 'timestamp']
    MIN_CONFIDENCE = 0.7  # 70% OCR confidence threshold
    
    def __init__(self):
        self.ocr = PaymentOCR()
    
    def validate_qris_payment(self, image_path: str) -> Dict:
        """
        Automatically validate QRIS payment from screenshot
        Returns: {
            'is_valid': bool,
            'confidence': float,
            'amount': float,
            'timestamp': str,
            'payment_method': str,
            'validation_details': dict
        }
        """
        try:
            # Extract payment information using OCR
            ocr_data = self.ocr.extract_payment_info(image_path)
            
            # Check if extraction was successful
            if not ocr_data.get('success', False):
                return {
                    'is_valid': False,
                    'confidence': 0,
                    'error': ocr_data.get('error', 'Unknown error'),
                    'validation_details': {
                        'reason': 'OCR extraction failed'
                    }
                }
            
            # Validate extracted data
            validation_result = self._validate_extracted_data(ocr_data, image_path)
            
            return validation_result
            
        except Exception as e:
            return {
                'is_valid': False,
                'confidence': 0,
                'error': str(e),
                'validation_details': {
                    'reason': 'Validation error'
                }
            }
    
    def _validate_extracted_data(self, ocr_data: Dict, image_path: str) -> Dict:
        """Validate the extracted payment data against QRIS rules"""
        
        validation_details = {
            'amount_valid': False,
            'timestamp_valid': False,
            'payment_method_detected': False,
            'qris_indicators_found': False,
            'image_quality': 0,
        }
        
        # 1. Check amount
        amount = ocr_data.get('amount')
        amount_valid = amount is not None and amount > 0
        validation_details['amount_valid'] = amount_valid
        
        # 2. Check timestamp
        timestamp = ocr_data.get('timestamp')
        timestamp_valid = self._validate_timestamp(timestamp)
        validation_details['timestamp_valid'] = timestamp_valid
        
        # 3. Check payment method
        payment_method = ocr_data.get('bank', 'Unknown')
        payment_method_detected = payment_method != 'Unknown'
        validation_details['payment_method_detected'] = payment_method_detected
        
        # 4. Check for QRIS indicators in text
        qris_found = self._check_qris_indicators(ocr_data)
        validation_details['qris_indicators_found'] = qris_found
        
        # 5. Check image quality
        image_quality = self._check_image_quality(image_path)
        validation_details['image_quality'] = image_quality
        
        # Calculate overall confidence
        ocr_confidence = ocr_data.get('confidence', 0)
        
        # Validation logic for QRIS
        is_valid = (
            amount_valid and 
            timestamp_valid and 
            (payment_method_detected or qris_found) and
            image_quality >= 0.5 and
            ocr_confidence >= self.MIN_CONFIDENCE
        )
        
        # Calculate overall confidence score
        confidence_score = self._calculate_confidence(
            ocr_confidence,
            amount_valid,
            timestamp_valid,
            payment_method_detected,
            qris_found,
            image_quality
        )
        
        return {
            'is_valid': is_valid,
            'confidence': round(confidence_score, 2),
            'amount': amount,
            'timestamp': timestamp,
            'payment_method': payment_method,
            'bank': ocr_data.get('bank'),
            'reference': ocr_data.get('reference'),
            'validation_details': validation_details,
            'ocr_confidence': round(ocr_confidence, 2)
        }
    
    def _validate_timestamp(self, timestamp: Optional[str]) -> bool:
        """Validate if timestamp is recent and properly formatted"""
        if not timestamp:
            return False
        
        try:
            # Try to parse various date formats
            date_formats = [
                '%d/%m/%Y %H:%M',
                '%d-%m-%Y %H:%M',
                '%Y/%m/%d %H:%M',
                '%d %B %Y %H:%M',
                '%d/%m/%Y',
                '%Y-%m-%d'
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(timestamp[:16], fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                return False
            
            # Check if timestamp is within last 24 hours
            time_diff = datetime.now() - parsed_date
            is_recent = time_diff.total_seconds() < 86400  # 24 hours
            
            return is_recent
        except Exception:
            return False
    
    def _check_qris_indicators(self, ocr_data: Dict) -> bool:
        """Check if QRIS or QR payment indicators are present"""
        bank = ocr_data.get('bank', '').lower()
        reference = ocr_data.get('reference', '').lower()
        
        # Check if any QRIS keywords are present
        for keyword in self.QRIS_KEYWORDS:
            if keyword in bank or keyword in reference:
                return True
        
        return False
    
    def _check_image_quality(self, image_path: str) -> float:
        """Check image quality for OCR accuracy"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return 0
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Check blur (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_score = min(1.0, laplacian_var / 1000.0)
            
            # Check brightness
            brightness = np.mean(gray) / 255.0
            brightness_score = 1.0 if 0.3 <= brightness <= 0.9 else 0.5
            
            # Check contrast
            contrast = np.std(gray) / 255.0
            contrast_score = min(1.0, contrast / 0.3)
            
            # Combined quality score
            quality_score = (blur_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
            
            return round(quality_score, 2)
        except Exception:
            return 0.5
    
    def _calculate_confidence(
        self,
        ocr_confidence: float,
        amount_valid: bool,
        timestamp_valid: bool,
        payment_method_detected: bool,
        qris_found: bool,
        image_quality: float
    ) -> float:
        """Calculate overall confidence score for validation"""
        
        # Weighted confidence calculation
        weights = {
            'ocr': 0.30,
            'amount': 0.25,
            'timestamp': 0.20,
            'payment_method': 0.15,
            'image_quality': 0.10
        }
        
        score = (
            ocr_confidence * weights['ocr'] +
            (1.0 if amount_valid else 0.0) * weights['amount'] +
            (1.0 if timestamp_valid else 0.0) * weights['timestamp'] +
            (1.0 if (payment_method_detected or qris_found) else 0.0) * weights['payment_method'] +
            image_quality * weights['image_quality']
        )
        
        return score
