# Quick Start Script - Run Flutter App
# This script runs the Flutter mobile app

Write-Host "📱 Starting Flutter Mobile App..." -ForegroundColor Cyan
Write-Host ""

# Check if Flutter is installed
try {
    flutter --version | Out-Null
    Write-Host "✅ Flutter found" -ForegroundColor Green
} catch {
    Write-Host "❌ Flutter not installed!" -ForegroundColor Red
    Write-Host "Download from: https://docs.flutter.dev/get-started/install" -ForegroundColor Yellow
    exit 1
}

# Navigate to mobile app
cd mobile_app

# Check if dependencies are installed
if (-not (Test-Path "pubspec.lock")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    flutter pub get
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Available devices:" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
flutter devices

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Starting app..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Login credentials:" -ForegroundColor Yellow
Write-Host "   Username: demo" -ForegroundColor White
Write-Host "   Password: demo123" -ForegroundColor White
Write-Host ""
Write-Host "Press 'r' to hot reload | 'R' to hot restart | 'q' to quit" -ForegroundColor Gray
Write-Host ""

flutter run
