import easyocr
import cv2
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import math
import os
import time

class BookReportOCR:
    def __init__(self):
        # Use EasyOCR optimized for handwritten documents
        self.backend = "EASY"
        
        # Initialize EasyOCR with Indonesian and English, optimized for handwriting
        self.reader = easyocr.Reader(
            ['id', 'en'],
            gpu=False,
            verbose=False
        )

        # Lower confidence threshold for handwritten text (but filter garbage)
        self.min_confidence = 0.3
        
    def _deskew(self, gray: np.ndarray) -> np.ndarray:
        """Deskew using Hough lines; fall back to original on failure"""
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        if lines is None:
            return gray
        angles = []
        for rho, theta in lines[:, 0]:
            angle = (theta * 180 / np.pi) - 90
            if -45 < angle < 45:
                angles.append(angle)
        if not angles:
            return gray
        median_angle = np.median(angles)
        (h, w) = gray.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
        return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results on handwritten documents"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Deskew to straighten handwriting
        gray = self._deskew(gray)

        # Normalize lighting and contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        norm = clahe.apply(gray)

        # Bilateral filter for edge-preserving smoothing (good for handwriting)
        bilateral = cv2.bilateralFilter(norm, 9, 75, 75)

        # Adaptive threshold for uneven lighting (better for handwritten documents)
        thresh = cv2.adaptiveThreshold(
            bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
        )

        # Light denoise
        denoised = cv2.fastNlMeansDenoising(thresh, h=15)

        # Slight dilation to strengthen strokes (important for thin handwriting)
        kernel = np.ones((2, 2), np.uint8)
        enhanced = cv2.dilate(denoised, kernel, iterations=1)

        return enhanced
    
    def extract_text_with_positions(self, image_path: str) -> List[Tuple[str, Tuple[int, int], float]]:
        """Extract text with their positions from image using EasyOCR optimized for handwriting"""
        image = cv2.imread(image_path)
        if image is None:
            return []

        processed = self.preprocess_image(image)

        # EasyOCR format: ((x1,y1),(x2,y2),(x3,y3),(x4,y4)), text, confidence
        results = self.reader.readtext(processed, detail=1, paragraph=False)

        text_positions = []
        for detection in results:
            bbox, text, confidence = detection
            
            # Filter out obviously bad detections
            if confidence < self.min_confidence or not text.strip():
                continue
            # Single character needs higher confidence to avoid noise
            if len(text.strip()) == 1 and confidence < 0.65:
                continue
            
            # Calculate center from bounding box coordinates
            bbox_array = np.array(bbox)
            center_y = int(np.mean(bbox_array[:, 1]))
            center_x = int(np.mean(bbox_array[:, 0]))
            text_positions.append((text, (center_y, center_x), confidence))

        # Deduplicate near-identical centers (keep higher confidence)
        dedup = {}
        for text, (y, x), conf in text_positions:
            # Cluster by 6px grid for handwritten text deduplication
            key = (round(y / 6), round(x / 6))
            if key not in dedup or dedup[key][2] < conf:
                dedup[key] = (text, (y, x), conf)

        merged = list(dedup.values())
        merged.sort(key=lambda x: (x[1][0], x[1][1]))
        return merged
    
    def detect_table_structure(self, text_positions: List[Tuple[str, Tuple[int, int], float]]) -> List[List[str]]:
        """Detect table structure from positioned text with adaptive row/col grouping"""
        if not text_positions:
            return []

        # Adaptive row threshold based on median vertical gap
        ys = [y for _, (y, _), _ in text_positions]
        ys_sorted = sorted(ys)
        gaps = [ys_sorted[i + 1] - ys_sorted[i] for i in range(len(ys_sorted) - 1)]
        median_gap = np.median(gaps) if gaps else 30
        y_threshold = max(15, min(50, median_gap * 1.3))

        rows = []
        current_row = []
        previous_y = None

        for text, (y, x), confidence in text_positions:
            if previous_y is None or abs(y - previous_y) < y_threshold:
                current_row.append((text, x, confidence))
            else:
                if current_row:
                    current_row.sort(key=lambda item: item[1])
                    rows.append([item[0] for item in current_row])
                current_row = [(text, x, confidence)]
            previous_y = y

        if current_row:
            current_row.sort(key=lambda item: item[1])
            rows.append([item[0] for item in current_row])

        # Adaptive column detection using X-gap clustering for handwritten documents
        # This is better for handwriting where column alignment may be loose
        xs = [x for _, _, (_, x), _ in [(None, None, (0, x), None) for _, (_, x), _ in text_positions]]
        
        if xs and len(xs) > 1:
            xs_sorted = sorted(xs)
            x_gaps = [xs_sorted[i + 1] - xs_sorted[i] for i in range(len(xs_sorted) - 1)]
            
            # Find significant gaps (potential column separators)
            if x_gaps:
                median_x_gap = np.median(x_gaps)
                # Column gap should be noticeably larger than character spacing
                col_gap_threshold = max(20, median_x_gap * 2)  # Handwriting needs more tolerance
                
                # Cluster X positions into columns
                column_clusters = []
                current_cluster = [xs_sorted[0]]
                
                for i in range(1, len(xs_sorted)):
                    if xs_sorted[i] - current_cluster[-1] < col_gap_threshold:
                        current_cluster.append(xs_sorted[i])
                    else:
                        if current_cluster:
                            col_center = np.median(current_cluster)
                            column_clusters.append(col_center)
                        current_cluster = [xs_sorted[i]]
                
                if current_cluster:
                    col_center = np.median(current_cluster)
                    column_clusters.append(col_center)
                
                # Re-align rows to detected columns (optional - mainly for cleanup)
                if len(column_clusters) > 1 and len(column_clusters) < len(rows[0]) if rows else 0:
                    # Only realign if we found fewer columns than row cells (reduces artifacts)
                    max_len = len(column_clusters)
                    aligned_rows = []
                    
                    for row in rows:
                        aligned_row = ["" for _ in range(max_len)]
                        
                        for cell_text in row:
                            # Find this cell's X position from original text_positions
                            for text, (_, cell_x), _ in text_positions:
                                if text == cell_text:
                                    # Assign to nearest column cluster
                                    nearest_col = min(range(len(column_clusters)), 
                                                     key=lambda i: abs(cell_x - column_clusters[i]))
                                    if aligned_row[nearest_col] == "":
                                        aligned_row[nearest_col] = cell_text
                                    else:
                                        aligned_row[nearest_col] += " " + cell_text
                                    break
                        
                        aligned_rows.append(aligned_row)
                    
                    rows = aligned_rows

        return rows
    
    def clean_and_normalize_data(self, rows: List[List[str]]) -> pd.DataFrame:
        """Clean and normalize extracted table data"""
        if not rows:
            return pd.DataFrame()
        
        # Determine number of columns (use most common row length)
        row_lengths = [len(row) for row in rows]
        num_columns = max(set(row_lengths), key=row_lengths.count) if row_lengths else 0
        
        if num_columns == 0:
            return pd.DataFrame()
        
        # Normalize rows to have same number of columns
        normalized_rows = []
        for row in rows:
            # Ensure row is a list of strings
            row = [str(item) if item else '' for item in row]
            
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
            try:
                # Try to convert to numeric
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except Exception:
                # Skip conversion if there's an issue
                pass
        
        return df
    
    def extract_table_from_image(self, image_path: str) -> Dict:
        """Main method to extract table from book report image"""
        start_time = time.time()
        try:
            # Extract text with positions
            text_positions = self.extract_text_with_positions(image_path)
            
            if not text_positions:
                return {
                    "success": False,
                    "error": "No text detected in image",
                    "rows_extracted": 0,
                    "columns_detected": 0,
                    "data": None,
                    "processing_time_seconds": round(time.time() - start_time, 2)
                }
            
            # Detect table structure
            rows = self.detect_table_structure(text_positions)
            
            if not rows:
                return {
                    "success": False,
                    "error": "Could not detect table structure",
                    "rows_extracted": 0,
                    "columns_detected": 0,
                    "data": None,
                    "processing_time_seconds": round(time.time() - start_time, 2)
                }
            
            # Create DataFrame
            df = self.clean_and_normalize_data(rows)
            
            # Calculate statistics
            rows_extracted = len(df)
            columns_detected = len(df.columns)

            # Create preview (first 5 rows)
            preview = df.head(5).to_string() if not df.empty else "No data"

            avg_conf = sum([conf for _, _, conf in text_positions]) / len(text_positions)

            return {
                "success": True,
                "rows_extracted": rows_extracted,
                "columns_detected": columns_detected,
                "data": df,
                "preview": preview,
                "confidence": round(float(avg_conf), 4),
                "processing_time_seconds": round(time.time() - start_time, 2)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rows_extracted": 0,
                "columns_detected": 0,
                "data": None,
                "processing_time_seconds": round(time.time() - start_time, 2)
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
