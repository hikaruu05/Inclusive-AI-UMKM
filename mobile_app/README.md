# Flutter Mobile App Setup Guide

## Prerequisites
- Flutter SDK 3.0+ installed
- Android Studio or VS Code with Flutter extension
- Android SDK or Xcode (for iOS)

## Installation

1. **Navigate to the mobile app directory:**
   ```bash
   cd mobile_app
   ```

2. **Install Flutter dependencies:**
   ```bash
   flutter pub get
   ```

3. **Create assets directory:**
   ```bash
   mkdir -p assets/images
   mkdir -p assets/icons
   ```

4. **Configure backend URL:**
   - Open `lib/services/api_service.dart`
   - Update `baseUrl` based on your setup:
     - Android Emulator: `http://10.0.2.2:8000`
     - iOS Simulator: `http://localhost:8000`
     - Physical device: `http://YOUR_COMPUTER_IP:8000`

5. **Run the app:**
   ```bash
   # For Android
   flutter run

   # For specific device
   flutter devices
   flutter run -d <device_id>
   ```

## Backend Setup

Before running the app, ensure the backend is running:

1. **Install new dependencies:**
   ```bash
   pip install python-jose[cryptography] passlib[bcrypt] openpyxl xlsxwriter
   ```

2. **Start the backend server:**
   ```bash
   cd backend
   python main.py
   ```

3. **Backend will be available at:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## Demo Account

Login credentials:
- Username: `demo`
- Password: `demo123`

## Features

### 1. **Dashboard**
- View today's statistics (revenue, transactions)
- Monitor pending payments
- Check low stock alerts
- Quick action buttons

### 2. **Payment Upload**
- Upload payment screenshots via camera or gallery
- Automatic OCR extraction
- Real-time validation with bank notifications
- View pending payments list

### 3. **Inventory Management**
- View all products with current stock
- Low stock indicators
- Search functionality
- Stock forecasting predictions
- Product details with analytics

### 4. **Book OCR to Excel** (NEW!)
- Capture handwritten book reports
- Automatic table detection and extraction
- Convert to structured Excel format
- Download and share Excel files

## Project Structure

```
mobile_app/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── providers/                # State management
│   │   ├── auth_provider.dart
│   │   ├── payment_provider.dart
│   │   └── inventory_provider.dart
│   ├── screens/                  # UI screens
│   │   ├── splash_screen.dart
│   │   ├── login_screen.dart
│   │   ├── home_screen.dart
│   │   ├── dashboard_screen.dart
│   │   ├── payment_upload_screen.dart
│   │   ├── inventory_screen.dart
│   │   └── book_ocr_screen.dart
│   └── services/                 # Backend communication
│       └── api_service.dart
└── pubspec.yaml                  # Dependencies
```

## API Endpoints Used

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/token` - Login and get token

### Payments
- `POST /api/payments/validate-screenshot` - Upload payment screenshot
- `GET /api/payments/pending` - Get pending payments
- `GET /api/payments/stats/today` - Today's statistics

### Inventory
- `GET /api/inventory/products` - Get all products
- `GET /api/inventory/low-stock` - Get low stock items
- `GET /api/inventory/forecast/{id}` - Get stock forecast

### OCR (NEW!)
- `POST /api/ocr/book-to-excel` - Convert book report to Excel
- `GET /api/ocr/download-excel/{file_id}` - Download Excel file
- `GET /api/ocr/files` - List converted files

## Troubleshooting

### Cannot connect to backend
- Ensure backend is running on port 8000
- Check firewall settings
- For physical device, use your computer's IP address
- For Android emulator, use `10.0.2.2` instead of `localhost`

### Image picker not working
- Android: Add permissions to `android/app/src/main/AndroidManifest.xml`:
  ```xml
  <uses-permission android:name="android.permission.CAMERA"/>
  <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
  <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
  ```

- iOS: Add to `ios/Runner/Info.plist`:
  ```xml
  <key>NSCameraUsageDescription</key>
  <string>Need camera access to capture payment screenshots</string>
  <key>NSPhotoLibraryUsageDescription</key>
  <string>Need photo library access to select images</string>
  ```

### Flutter build errors
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter run
```

## Building for Production

### Android APK
```bash
flutter build apk --release
```

### Android App Bundle (for Play Store)
```bash
flutter build appbundle --release
```

### iOS (requires Mac)
```bash
flutter build ios --release
```

## Next Steps

1. Add user registration screen
2. Implement profile settings
3. Add push notifications for payment alerts
4. Implement offline mode with local storage
5. Add charts for detailed analytics
6. Implement multi-language support (Indonesian/English)

## Support

For issues or questions:
- Check backend logs: `backend/logs/`
- Check API documentation: http://localhost:8000/docs
- Review Flutter logs: `flutter logs`
