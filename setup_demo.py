"""
Demo script to populate database with sample data for testing
Run this to quickly set up demo data for your hackathon presentation
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import SessionLocal, Product, Payment, BankNotification, StockMovement

def create_sample_products(db):
    """Create sample products for a typical Indonesian UMKM (coffee shop/warung)"""
    products = [
        {
            "name": "Kopi Susu",
            "category": "Minuman",
            "unit": "cup",
            "price": 15000,
            "current_stock": 50,
            "min_stock": 10
        },
        {
            "name": "Nasi Goreng",
            "category": "Makanan",
            "unit": "porsi",
            "price": 25000,
            "current_stock": 30,
            "min_stock": 5
        },
        {
            "name": "Teh Manis",
            "category": "Minuman",
            "unit": "cup",
            "price": 8000,
            "current_stock": 40,
            "min_stock": 10
        },
        {
            "name": "Gula Pasir",
            "category": "Bahan Baku",
            "unit": "kg",
            "price": 15000,
            "current_stock": 8,  # Low stock for demo
            "min_stock": 10
        },
        {
            "name": "Kopi Bubuk",
            "category": "Bahan Baku",
            "unit": "kg",
            "price": 85000,
            "current_stock": 15,
            "min_stock": 5
        },
        {
            "name": "Mi Goreng",
            "category": "Makanan",
            "unit": "porsi",
            "price": 15000,
            "current_stock": 25,
            "min_stock": 5
        }
    ]
    
    print("📦 Creating sample products...")
    for prod_data in products:
        product = Product(**prod_data)
        db.add(product)
    
    db.commit()
    print(f"✅ Created {len(products)} products")

def create_sample_payments(db):
    """Create sample payment records"""
    payments_data = [
        {
            "amount": 50000,
            "ocr_amount": 50000,
            "reference_number": "BCX123456",
            "ocr_reference": "BCX123456",
            "payment_date": datetime.utcnow() - timedelta(hours=2),
            "ocr_date": datetime.utcnow() - timedelta(hours=2),
            "is_verified": True,
            "verified_at": datetime.utcnow() - timedelta(hours=2),
            "customer_name": "Budi Santoso",
            "ocr_confidence": 0.92
        },
        {
            "amount": 75000,
            "ocr_amount": 75000,
            "reference_number": "GP789ABC",
            "ocr_reference": "GP789ABC",
            "payment_date": datetime.utcnow() - timedelta(hours=1),
            "ocr_date": datetime.utcnow() - timedelta(hours=1),
            "is_verified": True,
            "verified_at": datetime.utcnow() - timedelta(hours=1),
            "customer_name": "Siti Aminah",
            "ocr_confidence": 0.88
        },
        {
            "amount": 30000,
            "ocr_amount": 30000,
            "reference_number": "QRIS001",
            "ocr_reference": "QRIS001",
            "payment_date": datetime.utcnow() - timedelta(minutes=30),
            "ocr_date": datetime.utcnow() - timedelta(minutes=30),
            "is_verified": False,  # Pending verification
            "customer_name": "Ahmad Rizki",
            "ocr_confidence": 0.85
        }
    ]
    
    print("💰 Creating sample payments...")
    for payment_data in payments_data:
        payment = Payment(**payment_data)
        db.add(payment)
    
    db.commit()
    print(f"✅ Created {len(payments_data)} payments")

def create_sample_notifications(db):
    """Create sample bank notifications"""
    notifications_data = [
        {
            "source": "BCA",
            "raw_text": "Dana Masuk Rp 50.000,00 dari Budi Santoso. 04/12/23 14:35:20 Ref: BCX123456",
            "amount": 50000,
            "transaction_date": datetime.utcnow() - timedelta(hours=2),
            "reference_number": "BCX123456",
            "sender_name": "Budi Santoso",
            "is_matched": True,
            "matched_at": datetime.utcnow() - timedelta(hours=2)
        },
        {
            "source": "GoPay",
            "raw_text": "Dana masuk Rp 75.500 dari Siti Aminah 4 Des 2023 15:20 ID: GP789ABC",
            "amount": 75000,
            "transaction_date": datetime.utcnow() - timedelta(hours=1),
            "reference_number": "GP789ABC",
            "sender_name": "Siti Aminah",
            "is_matched": True,
            "matched_at": datetime.utcnow() - timedelta(hours=1)
        },
        {
            "source": "QRIS",
            "raw_text": "Pembayaran QRIS berhasil Rp 100.000 04/12/2023 16:45 NMID: QRIS999",
            "amount": 100000,
            "transaction_date": datetime.utcnow() - timedelta(minutes=15),
            "reference_number": "QRIS999",
            "is_matched": False  # Unmatched - waiting for screenshot
        }
    ]
    
    print("📱 Creating sample notifications...")
    for notif_data in notifications_data:
        notification = BankNotification(**notif_data)
        db.add(notification)
    
    db.commit()
    print(f"✅ Created {len(notifications_data)} notifications")

def create_sample_stock_movements(db):
    """Create sample stock movements for sales history"""
    print("📊 Creating sample stock movements...")
    
    products = db.query(Product).all()
    
    movements_count = 0
    for product in products:
        if product.category in ["Minuman", "Makanan"]:
            # Create sales history for the past 7 days
            for days_ago in range(7, 0, -1):
                # Random sales per day
                sales_count = random.randint(3, 10)
                
                for _ in range(sales_count):
                    quantity = random.uniform(1, 5)
                    previous_stock = product.current_stock + quantity
                    
                    movement = StockMovement(
                        product_id=product.id,
                        movement_type="sale",
                        quantity=-quantity,
                        previous_stock=previous_stock,
                        new_stock=product.current_stock,
                        reference_type="payment",
                        created_at=datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(8, 20))
                    )
                    
                    db.add(movement)
                    movements_count += 1
    
    db.commit()
    print(f"✅ Created {movements_count} stock movements")

def main():
    """Main demo setup function"""
    print("\n🚀 Setting up demo data for Inclusive AI UMKM")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("\n🗑️  Clearing existing data...")
        db.query(StockMovement).delete()
        db.query(Payment).delete()
        db.query(BankNotification).delete()
        db.query(Product).delete()
        db.commit()
        print("✅ Cleared")
        
        # Create sample data
        print("\n")
        create_sample_products(db)
        print()
        create_sample_payments(db)
        print()
        create_sample_notifications(db)
        print()
        create_sample_stock_movements(db)
        
        print("\n" + "=" * 50)
        print("✨ Demo data setup complete!")
        print("\n📊 Summary:")
        print(f"   Products: {db.query(Product).count()}")
        print(f"   Payments: {db.query(Payment).count()}")
        print(f"   Notifications: {db.query(BankNotification).count()}")
        print(f"   Stock Movements: {db.query(StockMovement).count()}")
        
        print("\n🎯 Next Steps:")
        print("   1. Start backend: cd backend && python main.py")
        print("   2. Start bot: cd bot && python telegram_bot.py")
        print("   3. Try these bot commands:")
        print("      /pendapatan - See today's revenue")
        print("      /stok - View all products")
        print("      /lowstok - See low stock alerts")
        print("\n   4. Test API: http://localhost:8000/docs")
        print("\n✨ Ready for demo!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
