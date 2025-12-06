import re
from datetime import datetime
from typing import Dict, Optional

class NotificationParser:
    """
    Parse bank/e-wallet notifications to extract payment information
    Supports various Indonesian banks and e-wallets
    """
    
    def __init__(self):
        # Bank-specific patterns
        self.bank_patterns = {
            "BCA": {
                "amount": r'(?:Rp|IDR)\s*([0-9,.]+)',
                "date": r'(\d{2}/\d{2}/\d{2,4})',
                "time": r'(\d{2}:\d{2}:\d{2})',
                "reference": r'Ref\s*:\s*([A-Z0-9]+)',
                "keywords": ["Dana Masuk", "Transfer", "Kredit"]
            },
            "Mandiri": {
                "amount": r'(?:Rp|IDR)\s*([0-9,.]+)',
                "date": r'(\d{2}/\d{2}/\d{2,4})',
                "time": r'(\d{2}:\d{2})',
                "reference": r'(?:Ref|No)\s*[:.]\s*([A-Z0-9]+)',
                "keywords": ["Mutasi Kredit", "Transfer Masuk"]
            },
            "BNI": {
                "amount": r'(?:Rp|IDR)\s*([0-9,.]+)',
                "date": r'(\d{2}-\d{2}-\d{2,4})',
                "time": r'(\d{2}:\d{2})',
                "reference": r'Ref\s*:\s*([A-Z0-9]+)',
                "keywords": ["Dana Masuk", "Kredit"]
            },
            "GoPay": {
                "amount": r'(?:Rp|IDR)\s*([0-9,.]+)',
                "date": r'(\d{1,2}\s+\w+\s+\d{4})',
                "time": r'(\d{2}:\d{2})',
                "reference": r'ID\s*:\s*([A-Z0-9-]+)',
                "keywords": ["Dana masuk", "Terima"]
            },
            "Dana": {
                "amount": r'(?:Rp|IDR)\s*([0-9,.]+)',
                "date": r'(\d{1,2}\s+\w+\s+\d{4})',
                "time": r'(\d{2}\.\d{2})',
                "reference": r'(?:Ref|ID)\s*:\s*([A-Z0-9-]+)',
                "keywords": ["Dana masuk", "Terima uang"]
            },
            "OVO": {
                "amount": r'(?:Rp|IDR)\s*([0-9,.]+)',
                "date": r'(\d{1,2}/\d{1,2}/\d{4})',
                "time": r'(\d{2}:\d{2})',
                "reference": r'TRX\s*ID\s*:\s*([A-Z0-9-]+)',
                "keywords": ["Dana masuk", "Terima"]
            },
            "QRIS": {
                "amount": r'(?:Rp|IDR)\s*([0-9,.]+)',
                "date": r'(\d{2}/\d{2}/\d{4})',
                "time": r'(\d{2}:\d{2})',
                "reference": r'(?:NMID|Ref)\s*:\s*([A-Z0-9-]+)',
                "keywords": ["Pembayaran", "QRIS", "Berhasil"]
            }
        }
    
    def detect_bank_source(self, text: str) -> Optional[str]:
        """
        Detect which bank/e-wallet the notification is from
        """
        text_lower = text.lower()
        
        # Check for keywords
        for bank, patterns in self.bank_patterns.items():
            for keyword in patterns["keywords"]:
                if keyword.lower() in text_lower:
                    return bank
        
        # Check for bank names
        bank_names = {
            "bca": "BCA",
            "mandiri": "Mandiri",
            "bni": "BNI",
            "gopay": "GoPay",
            "dana": "Dana",
            "ovo": "OVO",
            "qris": "QRIS"
        }
        
        for name, bank in bank_names.items():
            if name in text_lower:
                return bank
        
        return None
    
    def parse_amount(self, text: str, pattern: str) -> Optional[float]:
        """
        Extract amount using bank-specific pattern
        """
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Take the first/largest amount
            amounts = []
            for match in matches:
                clean = match.replace('.', '').replace(',', '')
                try:
                    amounts.append(float(clean))
                except ValueError:
                    continue
            
            if amounts:
                return max(amounts)
        
        return None
    
    def parse_datetime(self, text: str, date_pattern: str, time_pattern: str) -> Optional[datetime]:
        """
        Extract date and time using bank-specific patterns
        """
        date_match = re.search(date_pattern, text)
        time_match = re.search(time_pattern, text)
        
        if not date_match:
            return None
        
        date_str = date_match.group(1)
        time_str = time_match.group(1) if time_match else "00:00"
        
        # Handle different formats
        datetime_str = f"{date_str} {time_str}"
        
        # Indonesian month mapping
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'Mei': '05', 'Jun': '06', 'Jul': '07', 'Agu': '08',
            'Sep': '09', 'Okt': '10', 'Nov': '11', 'Des': '12'
        }
        
        for old, new in month_map.items():
            datetime_str = datetime_str.replace(old, new)
        
        # Try different datetime formats
        formats = [
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M",
            "%d/%m/%y %H:%M",
            "%d %m %Y %H:%M",
            "%d %m %Y %H.%M",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def parse_reference(self, text: str, pattern: str) -> Optional[str]:
        """
        Extract reference number using bank-specific pattern
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def parse_notification(self, raw_text: str, source: Optional[str] = None) -> Dict:
        """
        Main method: Parse notification text to extract payment info
        
        Args:
            raw_text: The raw notification text
            source: Bank/e-wallet name (optional, will auto-detect if not provided)
        
        Returns:
            Dict with parsed payment information
        """
        # Auto-detect source if not provided
        if not source:
            source = self.detect_bank_source(raw_text)
        
        if not source or source not in self.bank_patterns:
            # Use generic patterns if bank not recognized
            return self._parse_generic(raw_text)
        
        patterns = self.bank_patterns[source]
        
        # Extract components
        amount = self.parse_amount(raw_text, patterns["amount"])
        date_time = self.parse_datetime(raw_text, patterns["date"], patterns["time"])
        reference = self.parse_reference(raw_text, patterns["reference"])
        
        # Extract sender name if present
        sender_match = re.search(r'(?:dari|from)\s+([A-Z\s]+)', raw_text, re.IGNORECASE)
        sender = sender_match.group(1).strip() if sender_match else None
        
        return {
            "source": source,
            "amount": amount,
            "date": date_time or datetime.utcnow(),
            "reference": reference,
            "sender": sender,
            "parsed_successfully": bool(amount)
        }
    
    def _parse_generic(self, text: str) -> Dict:
        """
        Fallback generic parser when bank is not recognized
        """
        # Generic amount pattern
        amount_match = re.search(r'(?:Rp|IDR)\s*([0-9,.]+)', text, re.IGNORECASE)
        amount = None
        if amount_match:
            clean = amount_match.group(1).replace('.', '').replace(',', '')
            try:
                amount = float(clean)
            except ValueError:
                pass
        
        return {
            "source": "Unknown",
            "amount": amount,
            "date": datetime.utcnow(),
            "reference": None,
            "sender": None,
            "parsed_successfully": bool(amount)
        }

# For testing
if __name__ == "__main__":
    parser = NotificationParser()
    
    # Test notifications
    test_cases = [
        ("BCA", "Dana Masuk Rp 50.000,00 dari CUSTOMER A. 04/12/23 14:35:20 Ref: BCX123456"),
        ("GoPay", "Dana masuk Rp 75.500 dari Pembeli 4 Des 2023 15:20 ID: GP-2023-ABC123"),
        ("QRIS", "Pembayaran QRIS berhasil Rp 100.000 04/12/2023 16:45 NMID: QRIS123456"),
    ]
    
    for source, text in test_cases:
        print(f"\n=== Testing {source} ===")
        print(f"Text: {text}")
        result = parser.parse_notification(text, source)
        print(f"Result: {result}")
