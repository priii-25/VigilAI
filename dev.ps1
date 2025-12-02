# VigilAI - Development Commands
# Useful commands for development

Write-Host "🛠️  VigilAI Development Commands" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

function Show-Menu {
    Write-Host "Select an option:" -ForegroundColor Yellow
    Write-Host "1. Start all services (docker-compose)" -ForegroundColor White
    Write-Host "2. Stop all services" -ForegroundColor White
    Write-Host "3. View logs" -ForegroundColor White
    Write-Host "4. Restart services" -ForegroundColor White
    Write-Host "5. Run backend locally (dev mode)" -ForegroundColor White
    Write-Host "6. Run frontend locally (dev mode)" -ForegroundColor White
    Write-Host "7. Run database migrations" -ForegroundColor White
    Write-Host "8. Create new database migration" -ForegroundColor White
    Write-Host "9. Install backend dependencies" -ForegroundColor White
    Write-Host "10. Install frontend dependencies" -ForegroundColor White
    Write-Host "11. Run backend tests" -ForegroundColor White
    Write-Host "12. Clean up Docker volumes" -ForegroundColor White
    Write-Host "0. Exit" -ForegroundColor White
    Write-Host ""
}

do {
    Show-Menu
    $choice = Read-Host "Enter your choice"
    Write-Host ""

    switch ($choice) {
        "1" {
            Write-Host "🚀 Starting all services..." -ForegroundColor Cyan
            docker-compose up -d
            Write-Host "✅ Services started. Access at http://localhost:3000" -ForegroundColor Green
        }
        "2" {
            Write-Host "🛑 Stopping all services..." -ForegroundColor Cyan
            docker-compose down
            Write-Host "✅ Services stopped" -ForegroundColor Green
        }
        "3" {
            Write-Host "📊 Showing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
            docker-compose logs -f
        }
        "4" {
            Write-Host "🔄 Restarting services..." -ForegroundColor Cyan
            docker-compose restart
            Write-Host "✅ Services restarted" -ForegroundColor Green
        }
        "5" {
            Write-Host "🐍 Starting backend in dev mode..." -ForegroundColor Cyan
            Set-Location backend
            if (Test-Path "venv/Scripts/Activate.ps1") {
                .\venv\Scripts\Activate.ps1
                uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
            } else {
                Write-Host "❌ Virtual environment not found. Run option 9 first." -ForegroundColor Red
            }
            Set-Location ..
        }
        "6" {
            Write-Host "⚛️  Starting frontend in dev mode..." -ForegroundColor Cyan
            Set-Location frontend
            npm run dev
            Set-Location ..
        }
        "7" {
            Write-Host "🔄 Running database migrations..." -ForegroundColor Cyan
            Set-Location backend
            if (Test-Path "venv/Scripts/Activate.ps1") {
                .\venv\Scripts\Activate.ps1
                alembic upgrade head
                Write-Host "✅ Migrations completed" -ForegroundColor Green
            } else {
                Write-Host "❌ Virtual environment not found. Run option 9 first." -ForegroundColor Red
            }
            Set-Location ..
        }
        "8" {
            $message = Read-Host "Enter migration message"
            Write-Host "📝 Creating new migration..." -ForegroundColor Cyan
            Set-Location backend
            if (Test-Path "venv/Scripts/Activate.ps1") {
                .\venv\Scripts\Activate.ps1
                alembic revision --autogenerate -m "$message"
                Write-Host "✅ Migration created" -ForegroundColor Green
            } else {
                Write-Host "❌ Virtual environment not found. Run option 9 first." -ForegroundColor Red
            }
            Set-Location ..
        }
        "9" {
            Write-Host "📦 Installing backend dependencies..." -ForegroundColor Cyan
            Set-Location backend
            python -m venv venv
            .\venv\Scripts\Activate.ps1
            pip install -r requirements.txt
            pip install -r requirements-extra.txt
            Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
            Set-Location ..
        }
        "10" {
            Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Cyan
            Set-Location frontend
            npm install
            Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
            Set-Location ..
        }
        "11" {
            Write-Host "🧪 Running backend tests..." -ForegroundColor Cyan
            Set-Location backend
            if (Test-Path "venv/Scripts/Activate.ps1") {
                .\venv\Scripts\Activate.ps1
                pytest tests/ -v
            } else {
                Write-Host "❌ Virtual environment not found. Run option 9 first." -ForegroundColor Red
            }
            Set-Location ..
        }
        "12" {
            Write-Host "🧹 Cleaning up Docker volumes..." -ForegroundColor Yellow
            $confirm = Read-Host "This will delete all data. Continue? (y/n)"
            if ($confirm -eq "y") {
                docker-compose down -v
                Write-Host "✅ Volumes cleaned" -ForegroundColor Green
            } else {
                Write-Host "❌ Cancelled" -ForegroundColor Red
            }
        }
        "0" {
            Write-Host "👋 Goodbye!" -ForegroundColor Cyan
            break
        }
        default {
            Write-Host "❌ Invalid choice. Please try again." -ForegroundColor Red
        }
    }
    
    if ($choice -ne "0") {
        Write-Host ""
        Write-Host "Press any key to continue..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Clear-Host
    }
} while ($choice -ne "0")
