import easyocr
import cv2
import numpy as np
from PIL import Image
import pandas as pd
from typing import Dict, List, Tuple
import re
import io

class BookReportOCR:
    def __init__(self):
        # Initialize EasyOCR with Indonesian and English
        self.reader = easyocr.Reader(['id', 'en'])
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, h=10)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        return enhanced
    
    def extract_text_with_positions(self, image_path: str) -> List[Tuple[str, Tuple[int, int]]]:
        """Extract text with their positions from image"""
        # Read image
        image = cv2.imread(image_path)
        
        # Preprocess
        processed = self.preprocess_image(image)
        
        # Perform OCR
        results = self.reader.readtext(processed)
        
        # Extract text and positions
        text_positions = []
        for detection in results:
            bbox, text, confidence = detection
            # Get center position of bounding box
            center_y = int((bbox[0][1] + bbox[2][1]) / 2)
            center_x = int((bbox[0][0] + bbox[2][0]) / 2)
            text_positions.append((text, (center_y, center_x), confidence))
        
        # Sort by Y position (top to bottom), then X position (left to right)
        text_positions.sort(key=lambda x: (x[1][0], x[1][1]))
        
        return text_positions
    
    def detect_table_structure(self, text_positions: List[Tuple[str, Tuple[int, int]]]) -> List[List[str]]:
        """Detect table structure from positioned text"""
        if not text_positions:
            return []
        
        # Group texts by rows (similar Y positions)
        rows = []
        current_row = []
        previous_y = None
        y_threshold = 30  # Pixels threshold for same row
        
        for text, (y, x), confidence in text_positions:
            if previous_y is None or abs(y - previous_y) < y_threshold:
                current_row.append((text, x, confidence))
            else:
                if current_row:
                    # Sort by X position and extract text
                    current_row.sort(key=lambda item: item[1])
                    rows.append([item[0] for item in current_row])
                current_row = [(text, x, confidence)]
            previous_y = y
        
        # Add last row
        if current_row:
            current_row.sort(key=lambda item: item[1])
            rows.append([item[0] for item in current_row])
        
        return rows
    
    def clean_and_normalize_data(self, rows: List[List[str]]) -> pd.DataFrame:
        """Clean and normalize extracted table data"""
        if not rows:
            return pd.DataFrame()
        
        # Determine number of columns (use most common row length)
        row_lengths = [len(row) for row in rows]
        num_columns = max(set(row_lengths), key=row_lengths.count)
        
        # Normalize rows to have same number of columns
        normalized_rows = []
        for row in rows:
            if len(row) < num_columns:
                # Pad with empty strings
                row.extend([''] * (num_columns - len(row)))
            elif len(row) > num_columns:
                # Truncate
                row = row[:num_columns]
            normalized_rows.append(row)
        
        # Try to identify header row (usually first or second row)
        header_row = normalized_rows[0] if normalized_rows else []
        data_rows = normalized_rows[1:] if len(normalized_rows) > 1 else []
        
        # Create DataFrame
        if data_rows:
            df = pd.DataFrame(data_rows, columns=header_row if header_row else None)
        else:
            df = pd.DataFrame(columns=header_row if header_row else None)
        
        # Clean data
        df = df.replace('', np.nan)
        
        # Try to identify and convert numeric columns
        for col in df.columns:
            # Try to convert to numeric
            df[col] = pd.to_numeric(df[col], errors='ignore')
        
        return df
    
    def extract_table_from_image(self, image_path: str) -> Dict:
        """Main method to extract table from book report image"""
        try:
            # Extract text with positions
            text_positions = self.extract_text_with_positions(image_path)
            
            if not text_positions:
                return {
                    "success": False,
                    "error": "No text detected in image",
                    "rows_extracted": 0,
                    "columns_detected": 0,
                    "data": None
                }
            
            # Detect table structure
            rows = self.detect_table_structure(text_positions)
            
            if not rows:
                return {
                    "success": False,
                    "error": "Could not detect table structure",
                    "rows_extracted": 0,
                    "columns_detected": 0,
                    "data": None
                }
            
            # Create DataFrame
            df = self.clean_and_normalize_data(rows)
            
            # Calculate statistics
            rows_extracted = len(df)
            columns_detected = len(df.columns)
            
            # Create preview (first 5 rows)
            preview = df.head(5).to_string() if not df.empty else "No data"
            
            return {
                "success": True,
                "rows_extracted": rows_extracted,
                "columns_detected": columns_detected,
                "data": df,
                "preview": preview,
                "confidence": sum([conf for _, _, conf in text_positions]) / len(text_positions)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rows_extracted": 0,
                "columns_detected": 0,
                "data": None
            }
    
    def save_to_excel(self, df: pd.DataFrame, output_path: str):
        """Save DataFrame to Excel file"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Laporan')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Laporan']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
