"""
Test script to verify Supabase PostgreSQL connection and CRUD operations

Usage:
    python backend/scripts/test_supabase_connection.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

load_dotenv()

from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.models.database import (
    engine, Base, get_db, User, Product, Payment, 
    BankNotification, StockMovement, PaymentItem, Invoice
)

def test_connection():
    """Test basic database connection"""
    print("🔌 Testing Database Connection...")
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("   ✅ Database connection successful")
            return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def test_tables_exist():
    """Verify all tables exist"""
    print("\n📋 Checking Tables...")
    tables = [
        "users", "products", "notifications", "payments",
        "payment_items", "stock_movements", "invoices"
    ]
    
    all_exist = True
    with engine.connect() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   ✅ Table '{table}' exists ({count} records)")
            except Exception as e:
                print(f"   ❌ Table '{table}' not found: {e}")
                all_exist = False
    
    return all_exist

def test_crud_operations():
    """Test Create, Read, Update, Delete operations"""
    print("\n🧪 Testing CRUD Operations...")
    db = next(get_db())
    
    try:
        # CREATE - Test creating a product
        print("   📝 Testing CREATE...")
        test_product = Product(
            name="Test Product",
            category="Test",
            unit="pcs",
            price=10000.0,
            current_stock=10.0
        )
        db.add(test_product)
        db.commit()
        db.refresh(test_product)
        print(f"      ✅ Created product: {test_product.name} (ID: {test_product.id})")
        
        # READ - Test reading
        print("   📖 Testing READ...")
        found_product = db.query(Product).filter(Product.id == test_product.id).first()
        if found_product:
            print(f"      ✅ Read product: {found_product.name}")
        else:
            print("      ❌ Failed to read product")
            return False
        
        # UPDATE - Test updating
        print("   ✏️  Testing UPDATE...")
        found_product.price = 15000.0
        db.commit()
        db.refresh(found_product)
        if found_product.price == 15000.0:
            print(f"      ✅ Updated product price to {found_product.price}")
        else:
            print("      ❌ Failed to update product")
            return False
        
        # DELETE - Test deleting
        print("   🗑️  Testing DELETE...")
        db.delete(found_product)
        db.commit()
        deleted = db.query(Product).filter(Product.id == test_product.id).first()
        if not deleted:
            print("      ✅ Deleted product successfully")
        else:
            print("      ❌ Failed to delete product")
            return False
        
        print("   ✅ All CRUD operations passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ CRUD test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def test_relationships():
    """Test model relationships"""
    print("\n🔗 Testing Relationships...")
    db = next(get_db())
    
    try:
        # Create test data with relationships
        print("   📝 Creating test data with relationships...")
        
        # Create a product
        product = Product(
            name="Relationship Test Product",
            category="Test",
            unit="pcs",
            price=5000.0,
            current_stock=20.0
        )
        db.add(product)
        db.flush()
        
        # Create a payment
        payment = Payment(
            amount=10000.0,
            reference_number="TEST-REF-001",
            payment_date=datetime.now(),
            is_verified=True
        )
        db.add(payment)
        db.flush()
        
        # Create a payment item (relationship)
        payment_item = PaymentItem(
            payment_id=payment.id,
            product_id=product.id,
            quantity=2.0,
            unit_price=5000.0,
            subtotal=10000.0
        )
        db.add(payment_item)
        db.commit()
        
        # Test relationship access
        print("   🔍 Testing relationship access...")
        db.refresh(payment)
        db.refresh(product)
        
        if len(payment.items) > 0:
            print(f"      ✅ Payment.items relationship works ({len(payment.items)} items)")
        else:
            print("      ❌ Payment.items relationship failed")
            return False
        
        if len(product.payment_items) > 0:
            print(f"      ✅ Product.payment_items relationship works ({len(product.payment_items)} items)")
        else:
            print("      ❌ Product.payment_items relationship failed")
            return False
        
        # Cleanup
        db.delete(payment_item)
        db.delete(payment)
        db.delete(product)
        db.commit()
        
        print("   ✅ All relationship tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Relationship test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def test_transactions():
    """Test database transactions"""
    print("\n💾 Testing Transactions...")
    db = next(get_db())
    
    try:
        # Test rollback
        print("   🔄 Testing transaction rollback...")
        product = Product(
            name="Transaction Test Product",
            category="Test",
            unit="pcs",
            price=1000.0
        )
        db.add(product)
        db.flush()
        product_id = product.id
        
        # Rollback
        db.rollback()
        
        # Verify product was not committed
        check_product = db.query(Product).filter(Product.id == product_id).first()
        if not check_product:
            print("      ✅ Transaction rollback works")
        else:
            print("      ❌ Transaction rollback failed")
            return False
        
        # Test commit
        print("   ✅ Testing transaction commit...")
        product = Product(
            name="Transaction Test Product 2",
            category="Test",
            unit="pcs",
            price=2000.0
        )
        db.add(product)
        db.commit()
        product_id = product.id
        
        # Verify product was committed
        check_product = db.query(Product).filter(Product.id == product_id).first()
        if check_product:
            print("      ✅ Transaction commit works")
            # Cleanup
            db.delete(check_product)
            db.commit()
        else:
            print("      ❌ Transaction commit failed")
            return False
        
        print("   ✅ All transaction tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Transaction test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Supabase Connection & Functionality Test")
    print("=" * 60)
    
    # Check DATABASE_URL
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("\n❌ DATABASE_URL not found in environment variables")
        print("   Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    if not database_url.startswith("postgresql"):
        print(f"\n⚠️  DATABASE_URL is not PostgreSQL: {database_url}")
        print("   This test is for Supabase PostgreSQL. Skipping...")
        sys.exit(0)
    
    print(f"\n📡 Database URL: {database_url[:50]}...")
    
    results = []
    
    # Run tests
    results.append(("Connection", test_connection()))
    results.append(("Tables", test_tables_exist()))
    results.append(("CRUD Operations", test_crud_operations()))
    results.append(("Relationships", test_relationships()))
    results.append(("Transactions", test_transactions()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Supabase is ready to use.")
    else:
        print("❌ Some tests failed. Please review the errors above.")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

