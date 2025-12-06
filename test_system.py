"""
Quick test script to verify the system components work
Run this after installation to check everything is set up correctly
"""

import sys
import os

print("🧪 Running System Verification Tests\n")
print("=" * 60)

# Test 1: Check Python packages
print("\n1️⃣  Checking Python packages...")
try:
    import fastapi
    import sqlalchemy
    import easyocr
    import cv2
    import telegram
    print("   ✅ Core packages installed")
except ImportError as e:
    print(f"   ❌ Missing package: {e}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Check environment variables
print("\n2️⃣  Checking environment configuration...")
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "your_telegram_bot_token_here":
    print("   ✅ Telegram token configured")
else:
    print("   ⚠️  Telegram token not set (get from @BotFather)")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    print(f"   ✅ Database URL: {DATABASE_URL}")
else:
    print("   ℹ️  Using default SQLite database")

# Test 3: Check database
print("\n3️⃣  Checking database connection...")
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    from models.database import engine, Base, SessionLocal
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Test connection
    db = SessionLocal()
    db.execute("SELECT 1")
    db.close()
    
    print("   ✅ Database connected and tables created")
except Exception as e:
    print(f"   ❌ Database error: {e}")

# Test 4: Check OCR functionality
print("\n4️⃣  Testing OCR module...")
try:
    from ocr_module.payment_ocr import PaymentOCR
    ocr = PaymentOCR(languages=['en'], use_gpu=False)
    print("   ✅ OCR module loaded (models will download on first use)")
except Exception as e:
    print(f"   ❌ OCR error: {e}")

# Test 5: Check notification parser
print("\n5️⃣  Testing notification parser...")
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    from services.notification_parser import NotificationParser
    
    parser = NotificationParser()
    test_text = "Dana Masuk Rp 50.000,00 dari Test User. 04/12/23 14:35:20 Ref: TEST123"
    result = parser.parse_notification(test_text, "BCA")
    
    if result['amount'] == 50000:
        print("   ✅ Notification parser working")
        print(f"      Parsed: Rp {result['amount']:,.0f}")
    else:
        print("   ⚠️  Parser returned unexpected result")
except Exception as e:
    print(f"   ❌ Parser error: {e}")

# Test 6: Check API routes
print("\n6️⃣  Checking API structure...")
try:
    import backend.api.payments
    import backend.api.inventory
    import backend.api.notifications
    print("   ✅ All API modules present")
except Exception as e:
    print(f"   ❌ API module error: {e}")

# Summary
print("\n" + "=" * 60)
print("\n📊 Test Summary:")
print("\n✅ If all tests passed, you're ready to start!")
print("\n🚀 Next steps:")
print("   1. Set up demo data: python setup_demo.py")
print("   2. Start backend: cd backend && python main.py")
print("   3. Start bot: cd bot && python telegram_bot.py")
print("\n📖 See QUICKSTART.md for detailed instructions")
print("\n" + "=" * 60)
