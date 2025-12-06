# Migration Guide: Telegram Bot to Flutter Mobile App

## Changes Made

### 1. **New Mobile App Structure**
Created complete Flutter application in `mobile_app/` directory:
- Material Design 3 UI
- Provider state management
- JWT authentication
- Camera & gallery integration
- Excel file handling

### 2. **Backend Enhancements**

#### New Authentication System
- Added `User` model to database
- JWT token-based authentication
- Password hashing with bcrypt
- Demo user auto-creation (username: `demo`, password: `demo123`)

#### New OCR Feature for Book Reports
- `BookReportOCR` class for handwritten text extraction
- Table structure detection from images
- Excel export with openpyxl
- File download endpoints

#### New API Endpoints
```
POST /api/auth/register       - User registration
POST /api/auth/token          - Login (get JWT token)
GET  /api/auth/me             - Get current user info
POST /api/ocr/book-to-excel   - Convert book report to Excel
GET  /api/ocr/download-excel/{id} - Download Excel file
GET  /api/ocr/files           - List user's converted files
```

### 3. **Dependencies Added**

Python (requirements.txt):
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
openpyxl==3.1.2
xlsxwriter==3.1.9
```

Flutter (pubspec.yaml):
```yaml
provider: ^6.1.1
dio: ^5.4.0
image_picker: ^1.0.5
camera: ^0.10.5+7
fl_chart: ^0.65.0
excel: ^4.0.2
file_picker: ^6.1.1
```

## Migration Steps

### Step 1: Install New Dependencies
```bash
# Backend
pip install python-jose[cryptography] passlib[bcrypt] openpyxl xlsxwriter

# Flutter
cd mobile_app
flutter pub get
```

### Step 2: Update Database
The database will auto-migrate when you restart the backend.
```bash
cd backend
python main.py
```

This creates:
- `users` table
- Demo user account

### Step 3: Configure Flutter App
1. Open `mobile_app/lib/services/api_service.dart`
2. Update `baseUrl`:
   - For Android emulator: `http://10.0.2.2:8000`
   - For iOS simulator: `http://localhost:8000`
   - For physical device: `http://YOUR_IP:8000`

### Step 4: Run the Flutter App
```bash
cd mobile_app
flutter run
```

### Step 5: Test Features

1. **Authentication**
   - Login with demo/demo123
   - App shows splash → login → dashboard

2. **Payment Upload**
   - Navigate to "Upload" tab
   - Take photo or select from gallery
   - OCR extracts payment info automatically

3. **Inventory**
   - View products and stock levels
   - Check low stock alerts
   - Get forecasting predictions

4. **Book OCR (NEW!)**
   - Navigate to "Buku ke Excel" tab
   - Capture handwritten report page
   - Download converted Excel file

## Comparison: Telegram Bot vs Flutter App

| Feature | Telegram Bot | Flutter App |
|---------|--------------|-------------|
| Interface | Chat commands | Modern Material UI |
| Authentication | None | JWT with login screen |
| Image Upload | Send photo to bot | Camera + Gallery picker |
| Data Display | Text messages | Cards, charts, lists |
| Offline Mode | No | Possible (not yet implemented) |
| User Experience | Command-based | Touch-based navigation |
| Notifications | Telegram messages | Push notifications (future) |
| Book OCR | Not available | ✅ Available |

## Removed Files (Optional Cleanup)

You can safely remove Telegram bot files if no longer needed:
```bash
rm -rf bot/
```

But keeping them allows you to run both interfaces simultaneously!

## Running Both Interfaces

Backend supports both Telegram bot and Flutter app:

**Terminal 1 - Backend:**
```bash
python backend/main.py
```

**Terminal 2 - Telegram Bot (optional):**
```bash
python bot/telegram_bot.py
```

**Terminal 3 - Flutter App:**
```bash
cd mobile_app
flutter run
```

## Troubleshooting

### Cannot connect to backend from Flutter
- Check backend is running: http://localhost:8000/docs
- Verify API URL in `api_service.dart`
- For Android emulator, use `10.0.2.2` not `localhost`
- Check firewall allows port 8000

### Authentication fails
- Ensure backend has created demo user (check startup logs)
- Clear app data and retry
- Check token in SharedPreferences

### OCR not working
- Ensure image is clear and well-lit
- Check backend logs for errors
- Verify EasyOCR is installed: `pip install easyocr`

### Flutter build errors
```bash
flutter clean
flutter pub get
flutter run
```

## Next Development Steps

1. ✅ Basic authentication - DONE
2. ✅ Payment upload and validation - DONE
3. ✅ Inventory management - DONE
4. ✅ Book OCR to Excel - DONE
5. ⏳ User registration screen
6. ⏳ Profile settings page
7. ⏳ Push notifications
8. ⏳ Offline mode with local database
9. ⏳ Advanced analytics charts
10. ⏳ Multi-language support (ID/EN)

## API Changes Summary

### Existing Endpoints (still work)
All previous payment and inventory endpoints remain unchanged:
- `/api/payments/*`
- `/api/inventory/*`
- `/api/notifications/*`

### New Endpoints
- `/api/auth/*` - Authentication
- `/api/ocr/*` - Book report OCR

### Modified Behavior
- All endpoints now accept JWT tokens in `Authorization: Bearer <token>` header
- Unauthenticated requests will get 401 Unauthorized (except login/register)

## Database Schema Updates

New `users` table:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200),
    hashed_password VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Security Notes

⚠️ **Before production:**
1. Change `SECRET_KEY` in `backend/services/auth_service.py`
2. Use environment variables for secrets
3. Enable HTTPS
4. Add rate limiting
5. Implement refresh tokens
6. Add input validation
7. Set up proper CORS origins

## File Structure After Migration

```
inclusive-ai-umkm/
├── backend/                     # FastAPI backend
│   ├── api/
│   │   ├── auth.py             # NEW: Authentication
│   │   ├── ocr_reports.py      # NEW: Book OCR
│   │   ├── payments.py
│   │   ├── inventory.py
│   │   └── notifications.py
│   ├── services/
│   │   ├── auth_service.py     # NEW: JWT & auth logic
│   │   ├── book_report_ocr.py  # NEW: OCR processing
│   │   ├── payment_validator.py
│   │   └── inventory_manager.py
│   ├── models/
│   │   └── database.py         # UPDATED: Added User model
│   └── main.py                 # UPDATED: New routers
├── mobile_app/                 # NEW: Flutter application
│   ├── lib/
│   │   ├── main.dart
│   │   ├── providers/
│   │   ├── screens/
│   │   └── services/
│   ├── pubspec.yaml
│   └── README.md
├── bot/                        # OPTIONAL: Keep or remove
│   └── telegram_bot.py
├── requirements.txt            # UPDATED: New packages
└── README.md
```

## Questions & Support

**Q: Can I still use the Telegram bot?**  
A: Yes! Both interfaces work with the same backend.

**Q: Do I need to migrate existing data?**  
A: No, existing payments and inventory data remain unchanged.

**Q: How do I deploy the Flutter app?**  
A: Build APK with `flutter build apk --release`

**Q: Is this production-ready?**  
A: No, this is a hackathon prototype. See Security Notes above.

**Q: Can I customize the UI?**  
A: Yes! All Flutter screens are in `mobile_app/lib/screens/`

---

**Migration Status:** ✅ Complete

All features are functional. Test thoroughly before demo!
