"""
Migration script to migrate data from SQLite to Supabase PostgreSQL

Usage:
    python backend/scripts/migrate_to_supabase.py

Requirements:
    - SQLite database file at backend/umkm_db.sqlite
    - Supabase DATABASE_URL in .env file
    - All tables should be empty in Supabase (or use --force to overwrite)
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Import models
from backend.models.database import (BankNotification, Base, Invoice, Payment,
                                     PaymentItem, Product, StockMovement, User)


def get_sqlite_session():
    """Create SQLite session for reading data"""
    sqlite_path = Path(__file__).parent.parent / "umkm_db.sqlite"
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found at {sqlite_path}")
    
    sqlite_url = f"sqlite:///{sqlite_path}"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal

def get_supabase_session():
    """Create Supabase PostgreSQL session for writing data"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    
    if not database_url.startswith("postgresql"):
        raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
    
    engine = create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal

def migrate_users(sqlite_db, supabase_db, force=False):
    """Migrate users table"""
    print("\n📦 Migrating Users...")
    users = sqlite_db.query(User).all()
    
    if not users:
        print("   ℹ️  No users to migrate")
        return {}
    
    id_mapping = {}
    migrated = 0
    skipped = 0
    
    for user in users:
        try:
            # Check if user already exists
            existing = supabase_db.query(User).filter(
                User.username == user.username
            ).first()
            
            if existing and not force:
                print(f"   ⚠️  User '{user.username}' already exists, skipping")
                id_mapping[user.id] = existing.id
                skipped += 1
                continue
            
            new_user = User(
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                created_at=user.created_at
            )
            
            supabase_db.add(new_user)
            supabase_db.flush()  # Get the new ID
            id_mapping[user.id] = new_user.id
            migrated += 1
            
        except IntegrityError as e:
            print(f"   ❌ Error migrating user '{user.username}': {e}")
            supabase_db.rollback()
            skipped += 1
    
    supabase_db.commit()
    print(f"   ✅ Migrated {migrated} users, skipped {skipped}")
    return id_mapping

def migrate_products(sqlite_db, supabase_db, force=False):
    """Migrate products table"""
    print("\n📦 Migrating Products...")
    products = sqlite_db.query(Product).all()
    
    if not products:
        print("   ℹ️  No products to migrate")
        return {}
    
    id_mapping = {}
    migrated = 0
    skipped = 0
    
    for product in products:
        try:
            # Check if product already exists
            existing = supabase_db.query(Product).filter(
                Product.name == product.name
            ).first()
            
            if existing and not force:
                print(f"   ⚠️  Product '{product.name}' already exists, skipping")
                id_mapping[product.id] = existing.id
                skipped += 1
                continue
            
            new_product = Product(
                name=product.name,
                category=product.category,
                unit=product.unit,
                price=product.price,
                current_stock=product.current_stock,
                min_stock=product.min_stock,
                total_sold=product.total_sold,
                last_restocked_at=product.last_restocked_at,
                created_at=product.created_at
            )
            
            supabase_db.add(new_product)
            supabase_db.flush()
            id_mapping[product.id] = new_product.id
            migrated += 1
            
        except IntegrityError as e:
            print(f"   ❌ Error migrating product '{product.name}': {e}")
            supabase_db.rollback()
            skipped += 1
    
    supabase_db.commit()
    print(f"   ✅ Migrated {migrated} products, skipped {skipped}")
    return id_mapping

def migrate_notifications(sqlite_db, supabase_db, force=False):
    """Migrate bank notifications table"""
    print("\n📦 Migrating Bank Notifications...")
    notifications = sqlite_db.query(BankNotification).all()
    
    if not notifications:
        print("   ℹ️  No notifications to migrate")
        return {}
    
    id_mapping = {}
    migrated = 0
    skipped = 0
    
    for notification in notifications:
        try:
            new_notification = BankNotification(
                source=notification.source,
                raw_text=notification.raw_text,
                amount=notification.amount,
                transaction_date=notification.transaction_date,
                reference_number=notification.reference_number,
                sender_name=notification.sender_name,
                is_matched=notification.is_matched,
                matched_at=notification.matched_at,
                received_at=notification.received_at
            )
            
            supabase_db.add(new_notification)
            supabase_db.flush()
            id_mapping[notification.id] = new_notification.id
            migrated += 1
            
        except Exception as e:
            print(f"   ❌ Error migrating notification {notification.id}: {e}")
            supabase_db.rollback()
            skipped += 1
    
    supabase_db.commit()
    print(f"   ✅ Migrated {migrated} notifications, skipped {skipped}")
    return id_mapping

def migrate_payments(sqlite_db, supabase_db, notification_id_mapping, force=False):
    """Migrate payments table"""
    print("\n📦 Migrating Payments...")
    
    # Use raw SQL to read from SQLite (avoids column mismatch with bank_name)
    try:
        result = sqlite_db.execute(text("""
            SELECT id, amount, reference_number, payment_date, screenshot_path,
                   ocr_amount, ocr_date, ocr_reference, ocr_confidence,
                   is_verified, verified_at, notification_id, customer_name, notes, created_at
            FROM payments
        """))
        payment_rows = result.fetchall()
    except Exception as e:
        print(f"   ❌ Error reading payments from SQLite: {e}")
        return {}
    
    if not payment_rows:
        print("   ℹ️  No payments to migrate")
        return {}
    
    id_mapping = {}
    migrated = 0
    skipped = 0
    
    for row in payment_rows:
        try:
            # Map notification_id if it exists (index 11)
            mapped_notification_id = None
            if row[11] and row[11] in notification_id_mapping:
                mapped_notification_id = notification_id_mapping[row[11]]
            
            new_payment = Payment(
                amount=row[1],
                reference_number=row[2],
                payment_date=row[3],
                screenshot_path=row[4],
                ocr_amount=row[5],
                ocr_date=row[6],
                ocr_reference=row[7],
                ocr_confidence=row[8],
                is_verified=bool(row[9]) if row[9] is not None else False,
                verified_at=row[10],
                notification_id=mapped_notification_id,
                customer_name=row[12],
                bank_name=None,  # Not in old database, will be None
                notes=row[13],
                created_at=row[14]
            )
            
            supabase_db.add(new_payment)
            supabase_db.flush()
            id_mapping[row[0]] = new_payment.id  # Map old ID to new ID
            migrated += 1
            
        except Exception as e:
            print(f"   ❌ Error migrating payment {row[0]}: {e}")
            supabase_db.rollback()
            skipped += 1
    
    supabase_db.commit()
    print(f"   ✅ Migrated {migrated} payments, skipped {skipped}")
    return id_mapping

def migrate_payment_items(sqlite_db, supabase_db, payment_id_mapping, product_id_mapping, force=False):
    """Migrate payment items table"""
    print("\n📦 Migrating Payment Items...")
    items = sqlite_db.query(PaymentItem).all()
    
    if not items:
        print("   ℹ️  No payment items to migrate")
        return
    
    migrated = 0
    skipped = 0
    
    for item in items:
        try:
            # Map foreign keys
            if item.payment_id not in payment_id_mapping:
                print(f"   ⚠️  Payment {item.payment_id} not found, skipping item {item.id}")
                skipped += 1
                continue
            
            if item.product_id not in product_id_mapping:
                print(f"   ⚠️  Product {item.product_id} not found, skipping item {item.id}")
                skipped += 1
                continue
            
            new_item = PaymentItem(
                payment_id=payment_id_mapping[item.payment_id],
                product_id=product_id_mapping[item.product_id],
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal
            )
            
            supabase_db.add(new_item)
            migrated += 1
            
        except Exception as e:
            print(f"   ❌ Error migrating payment item {item.id}: {e}")
            supabase_db.rollback()
            skipped += 1
    
    supabase_db.commit()
    print(f"   ✅ Migrated {migrated} payment items, skipped {skipped}")

def migrate_stock_movements(sqlite_db, supabase_db, product_id_mapping, force=False):
    """Migrate stock movements table"""
    print("\n📦 Migrating Stock Movements...")
    movements = sqlite_db.query(StockMovement).all()
    
    if not movements:
        print("   ℹ️  No stock movements to migrate")
        return
    
    migrated = 0
    skipped = 0
    
    for movement in movements:
        try:
            if movement.product_id not in product_id_mapping:
                print(f"   ⚠️  Product {movement.product_id} not found, skipping movement {movement.id}")
                skipped += 1
                continue
            
            new_movement = StockMovement(
                product_id=product_id_mapping[movement.product_id],
                movement_type=movement.movement_type,
                quantity=movement.quantity,
                previous_stock=movement.previous_stock,
                new_stock=movement.new_stock,
                reference_type=movement.reference_type,
                reference_id=movement.reference_id,
                notes=movement.notes,
                created_at=movement.created_at
            )
            
            supabase_db.add(new_movement)
            migrated += 1
            
        except Exception as e:
            print(f"   ❌ Error migrating stock movement {movement.id}: {e}")
            supabase_db.rollback()
            skipped += 1
    
    supabase_db.commit()
    print(f"   ✅ Migrated {migrated} stock movements, skipped {skipped}")

def migrate_invoices(sqlite_db, supabase_db, force=False):
    """Migrate invoices table"""
    print("\n📦 Migrating Invoices...")
    invoices = sqlite_db.query(Invoice).all()
    
    if not invoices:
        print("   ℹ️  No invoices to migrate")
        return
    
    migrated = 0
    skipped = 0
    
    for invoice in invoices:
        try:
            new_invoice = Invoice(
                supplier_name=invoice.supplier_name,
                invoice_number=invoice.invoice_number,
                invoice_date=invoice.invoice_date,
                total_amount=invoice.total_amount,
                image_path=invoice.image_path,
                ocr_text=invoice.ocr_text,
                parsed_items=invoice.parsed_items,
                is_processed=invoice.is_processed,
                processed_at=invoice.processed_at,
                created_at=invoice.created_at
            )
            
            supabase_db.add(new_invoice)
            migrated += 1
            
        except Exception as e:
            print(f"   ❌ Error migrating invoice {invoice.id}: {e}")
            supabase_db.rollback()
            skipped += 1
    
    supabase_db.commit()
    print(f"   ✅ Migrated {migrated} invoices, skipped {skipped}")

def verify_migration(sqlite_db, supabase_db):
    """Verify migration by comparing record counts"""
    print("\n🔍 Verifying Migration...")
    
    tables = [
        ("Users", User, None),
        ("Products", Product, None),
        ("Notifications", BankNotification, None),
        ("Payments", Payment, "payments"),  # Use raw SQL for Payment (has bank_name column issue)
        ("Payment Items", PaymentItem, None),
        ("Stock Movements", StockMovement, None),
        ("Invoices", Invoice, None)
    ]
    
    all_match = True
    for name, model, table_name in tables:
        # Use raw SQL for Payment table to avoid bank_name column issue
        if table_name:
            sqlite_count = sqlite_db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        else:
            sqlite_count = sqlite_db.query(model).count()
        
        supabase_count = supabase_db.query(model).count()
        
        status = "✅" if sqlite_count == supabase_count else "❌"
        print(f"   {status} {name}: SQLite={sqlite_count}, Supabase={supabase_count}")
        
        if sqlite_count != supabase_count:
            all_match = False
    
    if all_match:
        print("\n   ✅ All record counts match!")
    else:
        print("\n   ⚠️  Some record counts don't match. Please review the migration.")
    
    return all_match

def main():
    """Main migration function"""
    print("=" * 60)
    print("🚀 SQLite to Supabase Migration Script")
    print("=" * 60)
    
    # Check for force flag
    force = "--force" in sys.argv
    
    try:
        # Create sessions
        print("\n📡 Connecting to databases...")
        sqlite_session = get_sqlite_session()
        supabase_session = get_supabase_session()
        
        sqlite_db = sqlite_session()
        supabase_db = supabase_session()
        
        print("   ✅ Connected to SQLite")
        print("   ✅ Connected to Supabase")
        
        # Migrate in order (respecting foreign key dependencies)
        print("\n" + "=" * 60)
        print("📦 Starting Data Migration")
        print("=" * 60)
        
        user_id_mapping = migrate_users(sqlite_db, supabase_db, force)
        product_id_mapping = migrate_products(sqlite_db, supabase_db, force)
        notification_id_mapping = migrate_notifications(sqlite_db, supabase_db, force)
        payment_id_mapping = migrate_payments(sqlite_db, supabase_db, notification_id_mapping, force)
        migrate_payment_items(sqlite_db, supabase_db, payment_id_mapping, product_id_mapping, force)
        migrate_stock_movements(sqlite_db, supabase_db, product_id_mapping, force)
        migrate_invoices(sqlite_db, supabase_db, force)
        
        # Verify migration
        print("\n" + "=" * 60)
        verify_migration(sqlite_db, supabase_db)
        
        print("\n" + "=" * 60)
        print("✅ Migration Complete!")
        print("=" * 60)
        print("\n📝 Next Steps:")
        print("   1. Update DATABASE_URL in .env to point to Supabase")
        print("   2. Test the application with: python test_system.py")
        print("   3. Verify all API endpoints work correctly")
        print("   4. Keep SQLite backup as fallback")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'sqlite_db' in locals():
            sqlite_db.close()
        if 'supabase_db' in locals():
            supabase_db.close()

if __name__ == "__main__":
    main()

