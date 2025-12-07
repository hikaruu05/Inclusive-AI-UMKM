import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.advanced_ocr import AdvancedOCR
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/ocr", tags=["OCR"])

# Create uploads directory
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "book_reports"
EXCEL_DIR = Path(__file__).parent.parent.parent / "uploads" / "excel_files"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXCEL_DIR.mkdir(parents=True, exist_ok=True)

# Store file mappings (in production, use database)
file_storage = {}

@router.post("/book-to-excel")
async def convert_book_to_excel(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Convert handwritten book report to Excel file
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    image_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    excel_path = EXCEL_DIR / f"{file_id}.xlsx"
    
    try:
        # Save uploaded image
        with open(image_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process image with OCR
        ocr_processor = AdvancedOCR()
        result = ocr_processor.extract_table_from_image(str(image_path))
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "OCR processing failed"))
        
        # Save to Excel
        df = result["data"]
        ocr_processor.save_to_excel(df, str(excel_path))
        
        # Store file mapping
        file_storage[file_id] = {
            "image_path": str(image_path),
            "excel_path": str(excel_path),
            "created_at": datetime.now().isoformat(),
            "username": current_user.username
        }
        
        return {
            "message": "Book report successfully converted to Excel",
            "file_id": file_id,
            "rows_extracted": result["rows_extracted"],
            "columns_detected": result["columns_detected"],
            "preview": result["preview"],
            "confidence": round(result["confidence"] * 100, 2),
            "download_url": f"/api/ocr/download-excel/{file_id}"
        }
        
    except Exception as e:
        # Cleanup on error
        if image_path.exists():
            os.remove(image_path)
        if excel_path.exists():
            os.remove(excel_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.get("/download-excel/{file_id}")
async def download_excel(file_id: str, current_user = Depends(get_current_user)):
    """
    Download converted Excel file
    """
    if file_id not in file_storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    excel_path = file_storage[file_id]["excel_path"]
    
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=404, detail="Excel file not found")
    
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"laporan_{file_id}.xlsx"
    )

@router.get("/files")
async def list_converted_files(current_user = Depends(get_current_user)):
    """
    List all converted files for current user
    """
    user_files = {
        fid: info for fid, info in file_storage.items()
        if info.get("username") == current_user.username
    }
    
    return {
        "count": len(user_files),
        "files": [
            {
                "file_id": fid,
                "created_at": info["created_at"],
                "download_url": f"/api/ocr/download-excel/{fid}"
            }
            for fid, info in user_files.items()
        ]
    }
