# VigilAI - Quick Start Commands

## 🚀 TLDR - Get Running in 5 Minutes

```powershell
# 1. Start Docker services (already done ✅)
docker compose -f docker-compose.simple.yml ps

# 2. Run automated setup
.\setup.ps1

# 3. Start backend (Terminal 1)
cd backend
.\venv\Scripts\Activate.ps1
uvicorn src.main:app --reload

# 4. Start celery (Terminal 2)
cd backend
.\venv\Scripts\Activate.ps1
celery -A src.services.celery_app worker --pool=solo --loglevel=info

# 5. Start frontend (Terminal 3)
cd frontend
npm run dev
```

## 🌐 Access URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- N8N: http://localhost:5678 (admin/admin)

## 🛑 Stop Everything
```powershell
# Stop application: Press Ctrl+C in each terminal
# Stop Docker: docker compose -f docker-compose.simple.yml down
```

## 📖 Full Documentation
See `SETUP_INSTRUCTIONS.md` for complete guide
