# Setup Script for UMKM Payment Validator
# Run this script to set up everything in one go

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  UMKM Payment Validator - Setup Script" -ForegroundColor Cyan
Write-Host "  Flutter Mobile App + Book OCR Feature" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Step 2: Check virtual environment
Write-Host ""
Write-Host "[2/5] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Step 3: Install Python dependencies
Write-Host ""
Write-Host "[3/5] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 4: Check Flutter
Write-Host ""
Write-Host "[4/5] Checking Flutter installation..." -ForegroundColor Yellow
try {
    $flutterVersion = flutter --version 2>&1 | Select-String "Flutter"
    Write-Host "✅ Flutter found: $flutterVersion" -ForegroundColor Green
    
    # Install Flutter dependencies
    Write-Host "Installing Flutter dependencies..." -ForegroundColor Yellow
    Set-Location mobile_app
    flutter pub get
    Set-Location ..
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Flutter dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Flutter dependencies installation had issues" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Flutter not found. You will need to install Flutter to run the mobile app" -ForegroundColor Yellow
    Write-Host "   Download from: https://docs.flutter.dev/get-started/install" -ForegroundColor Gray
}

# Step 5: Setup complete
Write-Host ""
Write-Host "[5/5] Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "uploads/book_reports" | Out-Null
New-Item -ItemType Directory -Force -Path "uploads/excel_files" | Out-Null
New-Item -ItemType Directory -Force -Path "uploads/screenshots" | Out-Null
Write-Host "✅ Directories created" -ForegroundColor Green

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start the backend:" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor White
Write-Host ""
Write-Host "2. Run the Flutter app (in new terminal):" -ForegroundColor Yellow
Write-Host "   cd mobile_app" -ForegroundColor White
Write-Host "   flutter run" -ForegroundColor White
Write-Host ""
Write-Host "3. Login with demo account:" -ForegroundColor Yellow
Write-Host "   Username: demo" -ForegroundColor White
Write-Host "   Password: demo123" -ForegroundColor White
Write-Host ""

Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "   - Quick Start: mobile_app/QUICKSTART.md" -ForegroundColor Gray
Write-Host "   - Full Guide: mobile_app/README.md" -ForegroundColor Gray
Write-Host "   - Migration: MIGRATION_GUIDE.md" -ForegroundColor Gray
Write-Host "   - Updates: UPDATE_SUMMARY.md" -ForegroundColor Gray
Write-Host ""

Write-Host "New Features:" -ForegroundColor Cyan
Write-Host "   Flutter Mobile App" -ForegroundColor Gray
Write-Host "   JWT Authentication" -ForegroundColor Gray
Write-Host "   Book OCR to Excel" -ForegroundColor Gray
Write-Host "   Camera Integration" -ForegroundColor Gray
Write-Host "   Payment Validation" -ForegroundColor Gray
Write-Host "   Inventory Forecasting" -ForegroundColor Gray
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Ready for hackathon! Good luck!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
