import easyocr
import cv2
import numpy as np
from datetime import datetime
import re
from typing import Dict, Optional

class PaymentOCR:
    """OCR service for extracting payment information from screenshots"""
    
    def __init__(self):
        # Initialize EasyOCR with Indonesian and English
        self.reader = easyocr.Reader(['id', 'en'], gpu=False)
        
    def extract_payment_info(self, image_path: str) -> Dict:
        """
        Extract payment details from screenshot
        Returns: {amount, timestamp, reference, bank, confidence}
        """
        try:
            # Read and preprocess image
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Enhance image quality
            enhanced = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Perform OCR
            results = self.reader.readtext(enhanced)
            
            # Extract text with confidence
            texts = []
            for bbox, text, confidence in results:
                texts.append((text, confidence))
            
            # Parse payment information
            amount = self.parse_amount(texts)
            timestamp = self.parse_date_time(texts)
            reference = self.parse_reference(texts)
            bank = self.detect_bank(texts)
            
            # Calculate average confidence
            avg_confidence = sum(c for _, c in texts) / len(texts) if texts else 0
            
            return {
                'amount': amount,
                'timestamp': timestamp,
                'reference': reference,
                'bank': bank,
                'confidence': round(avg_confidence, 2),
                'success': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'amount': None,
                'timestamp': None,
                'reference': None,
                'bank': None,
                'confidence': 0
            }
    
    def parse_amount(self, texts) -> Optional[float]:
        """Extract payment amount from text"""
        for text, _ in texts:
            # Remove non-numeric characters except dots and commas
            clean_text = re.sub(r'[^\d,.]', '', text)
            
            # Look for amounts (Rp patterns)
            if 'Rp' in text or 'IDR' in text:
                # Try to extract number
                numbers = re.findall(r'[\d,.]+', clean_text)
                if numbers:
                    try:
                        # Convert Indonesian format (1.000.000,00) to float
                        amount_str = numbers[0].replace('.', '').replace(',', '.')
                        return float(amount_str)
                    except:
                        pass
        
        # Try to find any large number (likely the amount)
        for text, _ in texts:
            numbers = re.findall(r'\d{3,}', text.replace('.', '').replace(',', ''))
            if numbers:
                try:
                    return float(numbers[0])
                except:
                    pass
        
        return None
    
    def parse_date_time(self, texts) -> Optional[str]:
        """Extract date and time from text"""
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # DD/MM/YYYY or DD-MM-YYYY
            r'\d{2,4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD
            r'\d{1,2}\s+\w+\s+\d{2,4}',         # DD Month YYYY
        ]
        
        time_pattern = r'\d{1,2}:\d{2}(:\d{2})?'
        
        found_date = None
        found_time = None
        
        for text, _ in texts:
            # Find date
            if not found_date:
                for pattern in date_patterns:
                    match = re.search(pattern, text)
                    if match:
                        found_date = match.group()
                        break
            
            # Find time
            if not found_time:
                match = re.search(time_pattern, text)
                if match:
                    found_time = match.group()
        
        if found_date:
            timestamp = f"{found_date} {found_time}" if found_time else found_date
            return timestamp
        
        return None
    
    def parse_reference(self, texts) -> Optional[str]:
        """Extract reference/transaction number"""
        ref_keywords = ['ref', 'referensi', 'no', 'trx', 'transaksi', 'id']
        
        for i, (text, _) in enumerate(texts):
            text_lower = text.lower()
            
            # Check if this text contains reference keyword
            if any(keyword in text_lower for keyword in ref_keywords):
                # Check next text for the actual reference number
                if i + 1 < len(texts):
                    next_text = texts[i + 1][0]
                    # Look for alphanumeric reference
                    if re.search(r'[A-Z0-9]{6,}', next_text):
                        return next_text
                
                # Or extract from same text
                ref_match = re.search(r'[A-Z0-9]{8,}', text)
                if ref_match:
                    return ref_match.group()
        
        return None
    
    def detect_bank(self, texts) -> Optional[str]:
        """Detect which bank/payment method from text"""
        banks = {
            'BCA': ['bca', 'bank central asia'],
            'Mandiri': ['mandiri', 'bank mandiri'],
            'BNI': ['bni', 'bank negara indonesia'],
            'BRI': ['bri', 'bank rakyat indonesia'],
            'GoPay': ['gopay', 'gojek'],
            'OVO': ['ovo'],
            'Dana': ['dana'],
            'ShopeePay': ['shopee', 'shopeepay'],
            'LinkAja': ['linkaja', 'link aja'],
            'QRIS': ['qris'],
        }
        
        all_text = ' '.join([text.lower() for text, _ in texts])
        
        for bank_name, keywords in banks.items():
            if any(keyword in all_text for keyword in keywords):
                return bank_name
        
        return 'Unknown'
