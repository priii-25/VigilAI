# VigilAI - Complete Setup Guide
# Run this script step by step

Write-Host "🚀 VigilAI - Complete Setup & Run Guide" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Core services are running:" -ForegroundColor Green
Write-Host "   - PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "   - Redis: localhost:6379" -ForegroundColor White
Write-Host "   - N8N: http://localhost:5678 (admin/admin)" -ForegroundColor White
Write-Host ""

Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host ""

Write-Host "STEP 1: Setup Backend" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host "cd backend"
Write-Host "python -m venv venv"
Write-Host ".\venv\Scripts\Activate.ps1"
Write-Host "pip install -r requirements.txt"
Write-Host "pip install -r requirements-extra.txt"
Write-Host ""

Write-Host "STEP 2: Configure Environment" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host "Make sure your .env file has:"
Write-Host "  DATABASE_URL=postgresql://vigilai:vigilai_password@localhost:5432/vigilai"
Write-Host "  REDIS_URL=redis://localhost:6379/0"
Write-Host "  GOOGLE_API_KEY=<your_key_here>"
Write-Host "  JWT_SECRET=<your_generated_secret>"
Write-Host ""

Write-Host "STEP 3: Run Database Migrations" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "cd backend"
Write-Host "alembic upgrade head"
Write-Host ""

Write-Host "STEP 4: Start Backend Server" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host "cd backend"
Write-Host "uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
Write-Host ""

Write-Host "STEP 5: Start Celery Worker (in new terminal)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "cd backend"
Write-Host ".\venv\Scripts\Activate.ps1"
Write-Host "celery -A src.services.celery_app worker --loglevel=info"
Write-Host ""

Write-Host "STEP 6: Setup Frontend (in new terminal)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "cd frontend"
Write-Host "npm install"
Write-Host "npm run dev"
Write-Host ""

Write-Host "🌐 Access Points:" -ForegroundColor Green
Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "   N8N:       http://localhost:5678" -ForegroundColor White
Write-Host ""

Write-Host "🛑 To stop Docker services:" -ForegroundColor Yellow
Write-Host "   docker compose -f docker-compose.simple.yml down" -ForegroundColor White
Write-Host ""

Write-Host "📖 Would you like to proceed with the setup? (Y/N)" -ForegroundColor Cyan
