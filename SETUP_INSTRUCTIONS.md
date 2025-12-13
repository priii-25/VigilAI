# VigilAI - Setup & Run Instructions (Bottom-Up)

## ✅ Current Status
- Docker Desktop is running
- Core services are running:
  - PostgreSQL: `localhost:5432`
  - Redis: `localhost:6379`
  - N8N: `http://localhost:5678` (admin/admin)

---

## 🎯 Quick Start (3 Methods)

### **Method 1: Automated Setup (Recommended)**
```powershell
# Run the automated setup script
.\setup.ps1

# Then follow the on-screen instructions to start services
```

### **Method 2: Manual Step-by-Step**
Follow the detailed steps below

### **Method 3: Using Start Script**
```powershell
.\start.ps1
```
(Note: This requires full Docker setup with application containers)

---

## 📋 Prerequisites Checklist

- [x] Docker Desktop installed and running
- [x] Python 3.10+ installed
- [x] Node.js 18+ installed
- [x] Git installed
- [ ] `.env` file configured (see below)

---

## 🔧 Step 1: Environment Configuration

### Create `.env` file:
```powershell
Copy-Item .env.example .env
notepad .env
```

### Minimum Required Settings:
```env
# Essential - Get free key at https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_actual_google_gemini_key

# Database (use these values as-is)
DATABASE_URL=postgresql://vigilai:vigilai_password@localhost:5432/vigilai
REDIS_URL=redis://localhost:6379/0

# Security (generate a secure random string)
JWT_SECRET=bLqJIv0X4Ti5nDGBVouajeYw98pWSrMs

# Application
APP_ENV=development
FRONTEND_URL=http://localhost:3000
LOG_LEVEL=INFO
```

### Generate a secure JWT Secret:
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

---

## 🐳 Step 2: Start Docker Services

```powershell
# Start PostgreSQL, Redis, and N8N
docker compose -f docker-compose.simple.yml up -d

# Verify services are running
docker compose -f docker-compose.simple.yml ps

# Check logs if needed
docker compose -f docker-compose.simple.yml logs -f
```

---

## 🐍 Step 3: Setup Backend

### 3.1 Create Virtual Environment
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3.2 Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-extra.txt
```

### 3.3 Install Playwright (for web scraping)
```powershell
playwright install chromium
```

### 3.4 Run Database Migrations
```powershell
alembic upgrade head
```

If you get an error, the database might be empty. Continue to start the server anyway.

---

## ⚛️ Step 4: Setup Frontend

### 4.1 Open a new terminal and navigate to frontend
```powershell
cd frontend
```

### 4.2 Install Node Dependencies
```powershell
npm install
```

---

## 🚀 Step 5: Run the Application

You'll need **3 terminals** running simultaneously:

### Terminal 1: Backend API Server
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Celery Worker (Background Tasks)
```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A src.services.celery_app worker --loglevel=info --pool=solo
```
Note: Use `--pool=solo` on Windows

### Terminal 3: Frontend Development Server
```powershell
cd frontend
npm run dev
```

---

## 🌐 Access the Application

Once all services are running:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost:3000 | (Create via API) |
| **Backend API** | http://localhost:8000 | - |
| **API Documentation** | http://localhost:8000/docs | Interactive Swagger UI |
| **N8N Workflows** | http://localhost:5678 | admin / admin |

---

## 👤 Step 6: Create First User

### Option 1: Using API Docs (Easiest)
1. Go to http://localhost:8000/docs
2. Find the `POST /api/v1/auth/register` endpoint
3. Click "Try it out"
4. Enter user details:
```json
{
  "email": "admin@vigilai.com",
  "password": "SecurePassword123!",
  "full_name": "Admin User"
}
```
5. Click "Execute"

### Option 2: Using Python Shell
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python
```

Then in Python:
```python
from src.core.database import SessionLocal
from src.models.user import User
from src.core.security import get_password_hash

db = SessionLocal()
admin = User(
    email="admin@vigilai.com",
    hashed_password=get_password_hash("SecurePassword123!"),
    full_name="Admin User",
    is_active=True
)
db.add(admin)
db.commit()
db.close()
print("✅ Admin user created!")
exit()
```

---

## 🎨 Step 7: Install Chrome Extension (Optional)

1. Open Chrome/Edge
2. Navigate to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select: `C:\Users\VICTUS\VigilAI\chrome-extension`

---

## 🛑 Stopping Services

### Stop Application Servers
Press `Ctrl+C` in each terminal running the services

### Stop Docker Services
```powershell
docker compose -f docker-compose.simple.yml down
```

### Stop and Remove Data
```powershell
docker compose -f docker-compose.simple.yml down -v
```
⚠️ This will delete all database data!

---

## 🔍 Troubleshooting

### Backend won't start
```powershell
# Check if Python virtual environment is activated
# You should see (venv) in your prompt

# Verify DATABASE_URL in .env
cat .env | Select-String "DATABASE_URL"

# Test database connection
docker exec -it vigilai_postgres psql -U vigilai -d vigilai -c "\dt"
```

### Frontend won't start
```powershell
# Clear node_modules and reinstall
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Celery won't start on Windows
```powershell
# Use solo pool for Windows
celery -A src.services.celery_app worker --loglevel=info --pool=solo
```

### Port already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
Stop-Process -Id PID -Force
```

### Database migration errors
```powershell
# Reset migrations
cd backend
alembic downgrade base
alembic upgrade head
```

---

## 📊 Verify Installation

### Check Backend Health
```powershell
Invoke-WebRequest -Uri http://localhost:8000/docs
```

### Check Frontend
```powershell
Start-Process http://localhost:3000
```

### Check Database
```powershell
docker exec -it vigilai_postgres psql -U vigilai -d vigilai -c "SELECT version();"
```

### Check Redis
```powershell
docker exec -it vigilai_redis redis-cli ping
```
Should return: `PONG`

---

## 🎯 What's Next?

1. **Add Competitors**: Use the API or frontend to add competitors to monitor
2. **Configure Integrations**: Add Slack, Notion, Salesforce API keys to `.env`
3. **Set up Scrapers**: Configure web scrapers for competitive intelligence
4. **Create Battlecards**: Generate dynamic battlecards from competitor data
5. **Setup N8N Workflows**: Create automation workflows at http://localhost:5678

---

## 📚 Project Structure

```
VigilAI/
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Config, database, security
│   │   ├── models/      # Database models
│   │   └── services/    # Business logic
│   └── alembic/         # Database migrations
├── frontend/            # Next.js frontend
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Next.js pages
│       └── lib/         # Utilities
└── chrome-extension/    # Chrome extension
```

---

## 🔗 Useful Commands

```powershell
# View backend logs
cd backend; uvicorn src.main:app --log-level debug

# View Docker logs
docker compose -f docker-compose.simple.yml logs -f

# Restart a Docker service
docker compose -f docker-compose.simple.yml restart postgres

# Check Python packages
cd backend; .\venv\Scripts\Activate.ps1; pip list

# Check Node packages
cd frontend; npm list --depth=0

# Run backend tests
cd backend; pytest tests/

# Build frontend for production
cd frontend; npm run build
```

---

## 🆘 Need Help?

- Check `Architecture.md` for system architecture
- Check `USER.md` for user documentation
- Check `PROJECT_COMPLETE.md` for project details
- Check API docs at http://localhost:8000/docs

---

## ✅ Success Checklist

- [ ] Docker services running (postgres, redis, n8n)
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed
- [ ] Database migrations completed
- [ ] Frontend dependencies installed
- [ ] Backend API server running on :8000
- [ ] Celery worker running
- [ ] Frontend dev server running on :3000
- [ ] Can access http://localhost:8000/docs
- [ ] Can access http://localhost:3000
- [ ] Admin user created

---

**🎉 Congratulations! Your VigilAI platform is now running!**
