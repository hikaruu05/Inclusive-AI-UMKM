import sys
from pathlib import Path

# Add parent directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
from datetime import datetime
from typing import Optional

from backend.api import payments, inventory, notifications, auth, ocr_reports
from backend.models.database import engine, Base, get_db
from backend.services.payment_validator import PaymentValidator
from backend.services.inventory_manager import InventoryManager

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inclusive AI UMKM - Payment & Inventory System",
    description="Automated payment validation and predictive inventory management for small businesses",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create demo user on startup
@app.on_event("startup")
async def startup_event():
    from backend.api.auth import create_demo_user
    db = next(get_db())
    create_demo_user(db)
    db.close()

# Include routers
app.include_router(auth.router, tags=["authentication"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(ocr_reports.router, tags=["ocr"])

@app.get("/")
async def root():
    return {
        "message": "Inclusive AI UMKM System",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "payments": "/api/payments",
            "inventory": "/api/inventory",
            "notifications": "/api/notifications",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
