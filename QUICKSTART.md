# Inclusive AI UMKM - Quick Start Guide

## Prerequisites

1. **Python 3.8+** installed
2. **Telegram Account** (for bot testing)
3. **API Keys** (Optional for full features):
   - OpenAI API Key (for invoice LLM parsing)
   - Google Gemini API Key (alternative to OpenAI)

## Installation Steps

### 1. Install Dependencies

```powershell
# Navigate to project directory
cd c:\inclusive-ai-umkm

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```powershell
# Copy example env file
cp .env.example .env

# Edit .env with your favorite editor
notepad .env
```

**Required Settings:**
- `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/BotFather) on Telegram

**Optional Settings:**
- `OPENAI_API_KEY`: For advanced invoice parsing
- `GEMINI_API_KEY`: Alternative to OpenAI

### 3. Initialize Database

```powershell
cd backend
python -c "from models.database import engine, Base; Base.metadata.create_all(bind=engine); print('✅ Database created!')"
```

### 4. Start the Backend API

```powershell
# In terminal 1
cd backend
python main.py
```

The API will start at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### 5. Start the Telegram Bot

```powershell
# In terminal 2 (new terminal)
cd bot
python telegram_bot.py
```

### 6. Test the Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start` to begin
4. Try sending a payment screenshot!

## Quick Demo

### Test Payment Validation

1. **Send payment screenshot** to bot
2. Bot extracts: Amount, Date, Reference
3. **Manually submit notification** via API:

```powershell
curl -X POST "http://localhost:8000/api/notifications/submit" `
  -H "Content-Type: application/json" `
  -d '{"source": "BCA", "raw_text": "Dana Masuk Rp 50.000 dari Customer A. 04/12/23 14:35:20 Ref: BCX123"}'
```

4. Bot auto-matches and verifies!

### Test Inventory Management

1. **Add a product** via API:

```powershell
curl -X POST "http://localhost:8000/api/inventory/products" `
  -H "Content-Type: application/json" `
  -d '{"name": "Kopi Susu", "price": 15000, "current_stock": 50, "unit": "pcs", "min_stock": 10}'
```

2. **Check stock** via bot: `/stok`
3. **Get forecast**: Visit `http://localhost:8000/api/inventory/forecast/1?days=7`

## Common Commands

### Bot Commands
- `/start` - Welcome message
- `/help` - Show all commands
- `/pendapatan` - Today's revenue
- `/stok` - View all products
- `/lowstok` - Low stock alerts
- `/pending` - Pending payments

### API Endpoints

**Payments:**
- `POST /api/payments/validate-screenshot` - Upload payment screenshot
- `GET /api/payments/pending` - List unverified payments
- `GET /api/payments/stats/today` - Today's statistics

**Inventory:**
- `GET /api/inventory/products` - List all products
- `POST /api/inventory/products` - Add new product
- `GET /api/inventory/low-stock` - Low stock alerts
- `POST /api/inventory/process-invoice` - Upload supplier invoice
- `GET /api/inventory/forecast/{product_id}` - Stock forecast

**Notifications:**
- `POST /api/notifications/submit` - Submit bank notification
- `GET /api/notifications/pending` - Unmatched notifications

## Troubleshooting

### Bot Not Responding
- Check if `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
- Ensure bot is running: `python bot/telegram_bot.py`
- Check bot logs for errors

### OCR Not Working
- Ensure image is clear and well-lit
- Install Tesseract separately if using pytesseract
- EasyOCR downloads models on first run (may take time)

### Database Errors
- Delete `umkm_db.sqlite` and recreate:
  ```powershell
  rm backend/umkm_db.sqlite
  python -c "from models.database import engine, Base; Base.metadata.create_all(bind=engine)"
  ```

## Next Steps for Hackathon

### Must-Have Features ✅
- [x] Payment OCR extraction
- [x] Notification parsing
- [x] Auto-matching system
- [x] Inventory tracking
- [x] Telegram bot interface

### Nice-to-Have Features 🚀
- [ ] WhatsApp integration (via Twilio)
- [ ] Android notification listener app
- [ ] Dashboard web UI
- [ ] Advanced fraud detection
- [ ] Multi-merchant support

### Demo Preparation

1. **Prepare sample data**: Add 3-5 products, make test payments
2. **Create demo flow**: Show customer → payment → verification → inventory update
3. **Prepare slides**: Show before/after comparison, time saved
4. **Practice pitch**: Focus on "inclusive" aspect - no new apps to learn!

## Tips for Winning

1. **Emphasize the Pain Point**: Manual verification wastes 30+ minutes/day
2. **Show Real Impact**: Demo with actual Indonesian payment apps (GoPay, Dana, QRIS)
3. **Highlight Inclusive UX**: Uses existing WhatsApp/Telegram - no learning curve
4. **Live Demo**: Show real payment screenshot → auto verification in real-time
5. **Market Size**: Indonesia has 64M+ UMKM businesses!

Good luck with your hackathon! 🚀
