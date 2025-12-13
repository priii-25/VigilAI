param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
Write-Host "`n🚀 VigilAI - Automated Setup`n" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) 
{
    Write-Host "❌ .env file not found! Please create it from .env.example first." -ForegroundColor Red
    Write-Host "Run: Copy-Item .env.example .env" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ .env file found" -ForegroundColor Green

# Verify Docker services
Write-Host "`n🐳 Checking Docker services..." -ForegroundColor Cyan
try {
    $dockerStatus = docker compose -f docker-compose.simple.yml ps --format json | ConvertFrom-Json
    if ($dockerStatus.Count -eq 3) {
        Write-Host "✅ All Docker services running" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Starting Docker services..." -ForegroundColor Yellow
        docker compose -f docker-compose.simple.yml up -d
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "❌ Failed to start Docker services" -ForegroundColor Red
    exit 1
}

# Setup Backend
if (-not $SkipBackend) {
    Write-Host "`n📦 Setting up Backend..." -ForegroundColor Cyan
    
    Set-Location backend
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        python -m venv venv
    }
    
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
    
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    if (Test-Path "requirements-extra.txt") {
        pip install -q -r requirements-extra.txt
    }
    
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    try {
        alembic upgrade head
        Write-Host "✅ Database migrations completed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Migration failed - database might need initialization" -ForegroundColor Yellow
    }
    
    Set-Location ..
    Write-Host "✅ Backend setup completed" -ForegroundColor Green
}

# Setup Frontend
if (-not $SkipFrontend) {
    Write-Host "`n📦 Setting up Frontend..." -ForegroundColor Cyan
    
    Set-Location frontend
    
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
        npm install
        Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
    }
    
    Set-Location ..
}

Write-Host "`n✅ Setup completed successfully!`n" -ForegroundColor Green

Write-Host "🚀 To start the application:" -ForegroundColor Cyan
Write-Host "`n1. Start Backend (in this terminal):" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White

Write-Host "`n2. Start Celery (in new terminal):" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "   celery -A src.services.celery_app worker --loglevel=info" -ForegroundColor White

Write-Host "`n3. Start Frontend (in another terminal):" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White

Write-Host "`n🌐 Access URLs:" -ForegroundColor Green
Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "   N8N:       http://localhost:5678 (admin/admin)" -ForegroundColor White
Write-Host ""
