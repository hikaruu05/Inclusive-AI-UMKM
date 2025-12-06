# Project Structure

```
inclusive-ai-umkm/
│
├── 📄 README.md                 # Main project documentation
├── 📄 QUICKSTART.md             # Quick start guide for setup
├── 📄 ARCHITECTURE.md           # System architecture details
├── 📄 DEMO_SCRIPT.md            # Hackathon presentation script
├── 📄 HACKATHON_CHECKLIST.md   # Pre-demo checklist
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env.example              # Environment variables template
├── 📄 .gitignore                # Git ignore rules
├── 📄 setup_demo.py             # Demo data population script
├── 📄 test_system.py            # System verification tests
│
├── 📁 backend/                  # FastAPI backend server
│   ├── 📄 main.py               # FastAPI application entry point
│   │
│   ├── 📁 api/                  # API route handlers
│   │   ├── __init__.py
│   │   ├── payments.py          # Payment validation endpoints
│   │   ├── inventory.py         # Inventory management endpoints
│   │   └── notifications.py     # Bank notification endpoints
│   │
│   ├── 📁 models/               # Database models
│   │   ├── __init__.py
│   │   └── database.py          # SQLAlchemy models & DB setup
│   │
│   └── 📁 services/             # Business logic services
│       ├── __init__.py
│       ├── payment_validator.py # Payment verification logic
│       ├── inventory_manager.py # Inventory & forecasting
│       └── notification_parser.py # Bank notification parsing
│
├── 📁 ocr_module/               # OCR processing
│   ├── __init__.py
│   └── payment_ocr.py           # EasyOCR payment extraction
│
├── 📁 bot/                      # Telegram bot
│   └── telegram_bot.py          # Bot handlers & commands
│
└── 📁 hackathon/                # (Original folder, can be removed)
```

## File Descriptions

### Root Level Files

**Documentation:**
- `README.md` - Overview, features, tech stack, demo flow
- `QUICKSTART.md` - Installation and setup instructions
- `ARCHITECTURE.md` - Technical architecture and design decisions
- `DEMO_SCRIPT.md` - Step-by-step hackathon presentation guide
- `HACKATHON_CHECKLIST.md` - Pre-demo preparation checklist

**Configuration:**
- `requirements.txt` - All Python package dependencies
- `.env.example` - Template for environment variables
- `.gitignore` - Files to exclude from git

**Scripts:**
- `setup_demo.py` - Populates database with sample data
- `test_system.py` - Verifies all components work correctly

### Backend (`/backend`)

**Main Application:**
- `main.py` - FastAPI app initialization, CORS setup, route registration

**API Endpoints (`/api`):**
- `payments.py` - Handle payment screenshot uploads, verification, statistics
- `inventory.py` - Product CRUD, stock management, forecasting
- `notifications.py` - Bank notification submission and matching

**Database (`/models`):**
- `database.py` - SQLAlchemy models for:
  - `Payment` - Payment records with OCR data
  - `BankNotification` - Bank/e-wallet notifications
  - `Product` - Inventory items
  - `StockMovement` - Stock change history
  - `Invoice` - Supplier invoices
  - `PaymentItem` - Line items in payments

**Business Logic (`/services`):**
- `payment_validator.py` - OCR extraction, amount/time matching, auto-verification
- `inventory_manager.py` - Stock tracking, invoice processing, predictive forecasting
- `notification_parser.py` - Multi-bank notification parsing (BCA, GoPay, Dana, etc.)

### OCR Module (`/ocr_module`)

- `payment_ocr.py` - EasyOCR integration for:
  - Image preprocessing
  - Text extraction
  - Amount/date/reference parsing
  - Pattern matching for Indonesian payment apps

### Bot (`/bot`)

- `telegram_bot.py` - Telegram bot with:
  - Command handlers (`/start`, `/stok`, `/pendapatan`, etc.)
  - Photo upload processing
  - Natural language queries
  - Interactive buttons

## Key Features by Component

### Payment Validation System
- **OCR Extraction**: Extract amount, date, reference from screenshots
- **Notification Parsing**: Parse bank SMS/notifications (10+ banks supported)
- **Auto-Matching**: Match payments with notifications within time window
- **Confidence Scoring**: Calculate match probability
- **Fraud Prevention**: Verify actual bank transactions

### Inventory Management
- **Product Tracking**: CRUD for products with stock levels
- **Auto-Deduction**: Reduce stock on verified payments
- **Low Stock Alerts**: Notify when below threshold
- **Invoice OCR**: Extract items from supplier invoices
- **LLM Parsing**: Use OpenAI/Gemini to structure invoice data

### Predictive Analytics
- **Sales Forecasting**: Time-series analysis of sales patterns
- **Stock Prediction**: Calculate when stock will run out
- **Order Recommendations**: Suggest reorder quantities
- **Historical Analysis**: Track sales trends

### Telegram Bot Interface
- **Natural Language**: Understand Indonesian queries
- **Photo Processing**: Handle payment & invoice uploads
- **Real-time Reports**: Daily revenue, stock status
- **Alerts**: Low stock, pending payments
- **No App Required**: Uses existing Telegram

## Data Flow Example

### Complete Payment Flow:

```
1. Customer pays via QRIS/GoPay/Dana
   ↓
2. Customer sends screenshot to merchant's Telegram
   ↓
3. Bot receives image → uploads to API
   ↓
4. OCR extracts: Rp 50,000 | 14:35 | REF123
   ↓
5. Stored in DB as "unverified"
   ↓
6. Merchant's phone receives bank notification
   ↓
7. Merchant forwards to bot (or auto-captured)
   ↓
8. Parser extracts: Rp 50,000 | 14:36 | REF123
   ↓
9. Validator matches (amount ✓, time ✓, ref ✓)
   ↓
10. Payment marked "verified"
   ↓
11. Inventory auto-updated (Kopi Susu -2)
   ↓
12. Bot replies: "✅ Payment verified! Order processing"
   ↓
13. Bot checks stock: "⚠️ Gula will run out in 3 days"
```

## Database Relationships

```
Payment (1) ←→ (1) BankNotification
Payment (1) ←→ (N) PaymentItem
PaymentItem (N) ←→ (1) Product
Product (1) ←→ (N) StockMovement
```

## API Usage Examples

**Upload Payment Screenshot:**
```bash
curl -X POST http://localhost:8000/api/payments/validate-screenshot \
  -F "file=@payment.jpg"
```

**Submit Bank Notification:**
```bash
curl -X POST http://localhost:8000/api/notifications/submit \
  -H "Content-Type: application/json" \
  -d '{"source": "BCA", "raw_text": "Dana Masuk Rp 50.000..."}'
```

**Get Today's Revenue:**
```bash
curl http://localhost:8000/api/payments/stats/today
```

**Check Low Stock:**
```bash
curl http://localhost:8000/api/inventory/low-stock
```

## Development Workflow

1. **Setup**: Install dependencies, configure `.env`
2. **Database**: Run `setup_demo.py` for sample data
3. **Backend**: Start FastAPI server (`python backend/main.py`)
4. **Bot**: Start Telegram bot (`python bot/telegram_bot.py`)
5. **Test**: Verify with `test_system.py`
6. **Demo**: Follow `DEMO_SCRIPT.md`

## Next Steps

### For Development:
1. Copy `.env.example` to `.env` and fill in your API keys
2. Run `pip install -r requirements.txt`
3. Run `python test_system.py` to verify setup
4. Run `python setup_demo.py` to populate demo data
5. Start building!

### For Hackathon:
1. Follow `QUICKSTART.md` for setup
2. Review `DEMO_SCRIPT.md` for presentation
3. Check `HACKATHON_CHECKLIST.md` before demo
4. Practice the demo 3-5 times

### For Production:
1. Review `ARCHITECTURE.md` for scaling strategies
2. Implement authentication & authorization
3. Add monitoring & logging
4. Set up CI/CD pipeline
5. Deploy to cloud provider

---

**Total Lines of Code**: ~3,500+  
**Languages**: Python, Markdown  
**Frameworks**: FastAPI, python-telegram-bot, SQLAlchemy, EasyOCR  
**Database**: SQLite (dev), PostgreSQL (prod)  
**License**: MIT (recommended for open source)
