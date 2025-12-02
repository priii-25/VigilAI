# VigilAI - Quick Start Script
# Run this after setting up your .env file

Write-Host "🚀 VigilAI Setup & Startup Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "📝 Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ .env file created. Please edit it with your API keys." -ForegroundColor Green
    Write-Host "📖 See USER.md for detailed setup instructions." -ForegroundColor Cyan
    exit
}

Write-Host "✅ .env file found" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "🐳 Starting Docker containers..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ All services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access your applications:" -ForegroundColor Cyan
    Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   N8N:       http://localhost:5678" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 View logs:" -ForegroundColor Cyan
    Write-Host "   docker-compose logs -f" -ForegroundColor White
    Write-Host ""
    Write-Host "🛑 Stop services:" -ForegroundColor Cyan
    Write-Host "   docker-compose down" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 For detailed setup instructions, see USER.md" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Failed to start services. Check the error messages above." -ForegroundColor Red
    Write-Host "💡 Common issues:" -ForegroundColor Yellow
    Write-Host "   - Make sure ports 3000, 5678, 5432, 6379, 8000 are available" -ForegroundColor White
    Write-Host "   - Check your .env file has all required values" -ForegroundColor White
    Write-Host "   - Review Docker logs: docker-compose logs" -ForegroundColor White
}
