import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from backend.models.database import get_db, Product, StockMovement, Invoice
from backend.services.inventory_manager import InventoryManager

router = APIRouter()
inventory_manager = InventoryManager()

class ProductCreate(BaseModel):
    name: str
    category: Optional[str] = None
    unit: str = "pcs"
    price: float
    current_stock: float = 0
    min_stock: float = 10

class ProductResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    unit: str
    price: float
    current_stock: float
    min_stock: float
    total_sold: float
    
    class Config:
        from_attributes = True

class StockAdjustment(BaseModel):
    product_id: int
    quantity: float
    movement_type: str  # "restock" or "adjustment"
    notes: Optional[str] = None

@router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Add new product to inventory
    """
    # Check if product already exists
    existing = db.query(Product).filter(Product.name == product.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already exists")
    
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return new_product

@router.get("/products", response_model=List[ProductResponse])
async def get_all_products(db: Session = Depends(get_db)):
    """
    Get all products in inventory
    """
    products = db.query(Product).all()
    return products

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get specific product details
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/adjust-stock")
async def adjust_stock(adjustment: StockAdjustment, db: Session = Depends(get_db)):
    """
    Manually adjust stock (restock or correction)
    """
    product = db.query(Product).filter(Product.id == adjustment.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    previous_stock = product.current_stock
    new_stock = previous_stock + adjustment.quantity
    
    # Create stock movement record
    movement = StockMovement(
        product_id=product.id,
        movement_type=adjustment.movement_type,
        quantity=adjustment.quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        reference_type="manual",
        notes=adjustment.notes
    )
    
    product.current_stock = new_stock
    if adjustment.movement_type == "restock":
        product.last_restocked_at = datetime.utcnow()
    
    db.add(movement)
    db.commit()
    
    return {
        "status": "success",
        "product": product.name,
        "previous_stock": previous_stock,
        "new_stock": new_stock,
        "change": adjustment.quantity
    }

@router.get("/low-stock")
async def get_low_stock_products(db: Session = Depends(get_db)):
    """
    Get products with stock below minimum threshold
    """
    low_stock = db.query(Product).filter(
        Product.current_stock <= Product.min_stock
    ).all()
    
    alerts = []
    for product in low_stock:
        alerts.append({
            "product_id": product.id,
            "name": product.name,
            "current_stock": product.current_stock,
            "min_stock": product.min_stock,
            "unit": product.unit,
            "alert": f"⚠️ {product.name} running low: {product.current_stock} {product.unit} left"
        })
    
    return {
        "total_alerts": len(alerts),
        "products": alerts
    }

@router.post("/process-invoice")
async def process_supplier_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload supplier invoice image and extract items using OCR + LLM
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded image
    import os
    upload_dir = "uploads/invoices"
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(upload_dir, f"{timestamp}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Process invoice with OCR + LLM
        invoice_data = await inventory_manager.process_invoice_image(file_path, db)
        
        return {
            "status": "success",
            "message": "Invoice processed successfully",
            "invoice_id": invoice_data["invoice_id"],
            "supplier": invoice_data.get("supplier"),
            "items_added": invoice_data.get("items_count", 0),
            "extracted_items": invoice_data.get("items", [])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invoice processing failed: {str(e)}")

@router.get("/forecast/{product_id}")
async def get_stock_forecast(
    product_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get predictive stock forecast for a product
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        forecast = await inventory_manager.forecast_stock_needs(product_id, days, db)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")

@router.get("/history/{product_id}")
async def get_stock_history(
    product_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get stock movement history for a product
    """
    movements = db.query(StockMovement).filter(
        StockMovement.product_id == product_id
    ).order_by(StockMovement.created_at.desc()).limit(limit).all()
    
    return {
        "product_id": product_id,
        "total_movements": len(movements),
        "history": [
            {
                "id": m.id,
                "type": m.movement_type,
                "quantity": m.quantity,
                "previous": m.previous_stock,
                "new": m.new_stock,
                "date": m.created_at.isoformat(),
                "notes": m.notes
            }
            for m in movements
        ]
    }
