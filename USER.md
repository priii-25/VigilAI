# VigilAI Setup and Configuration Guide

## Overview
VigilAI is a production-ready competitive intelligence platform with AIOps capabilities. This guide will help you set up and configure all necessary API keys and integrations.

---

## 🔧 Initial Setup

### 1. Environment Configuration

Copy the `.env.example` file to `.env`:
```powershell
Copy-Item .env.example .env
```

### 2. Required API Keys

You need to obtain and configure the following API keys:

#### **AI Services**
- **OpenAI API Key**: https://platform.openai.com/api-keys
- **Anthropic (Claude) API Key**: https://console.anthropic.com/
- **Perplexity API Key**: https://www.perplexity.ai/settings/api

#### **Integrations**
- **Notion API Key**: https://www.notion.so/my-integrations
- **Slack Bot Token**: https://api.slack.com/apps
- **Salesforce Credentials**: https://developer.salesforce.com/

---

## 📝 Configuration Steps

### 1. AI API Keys

#### OpenAI Setup
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key and add to `.env`:
```env
OPENAI_API_KEY=sk-...your-key-here
```

#### Anthropic (Claude) Setup
1. Visit https://console.anthropic.com/
2. Generate an API key
3. Add to `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-...your-key-here
```

#### Perplexity Setup
1. Go to https://www.perplexity.ai/settings/api
2. Generate API key
3. Add to `.env`:
```env
PERPLEXITY_API_KEY=pplx-...your-key-here
```

---

### 2. Database Configuration

#### PostgreSQL
The default docker-compose setup creates PostgreSQL automatically, but for production:

1. Create a PostgreSQL database
2. Update `.env`:
```env
DATABASE_URL=postgresql://username:password@host:5432/database_name
```

#### Redis
Default docker setup includes Redis. For external Redis:
```env
REDIS_URL=redis://host:6379/0
```

---

### 3. Notion Integration

#### Create Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it "VigilAI"
4. Select capabilities: Read content, Update content, Insert content
5. Copy the "Internal Integration Token"

#### Create Notion Database
1. Create a new page in Notion
2. Add a database (table view)
3. Add these properties:
   - Name (title)
   - Competitor (text)
   - Status (select: Draft, Published)
4. Click "..." → "Add connections" → Select "VigilAI"
5. Copy database ID from URL: `notion.so/.../{database_id}?v=...`

#### Update .env
```env
NOTION_API_KEY=secret_...your-integration-token
NOTION_DATABASE_ID=...your-database-id
```

---

### 4. Slack Integration

#### Create Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "VigilAI Bot"
4. Select your workspace

#### Configure Bot Permissions
1. Go to "OAuth & Permissions"
2. Add these Bot Token Scopes:
   - `chat:write`
   - `chat:write.public`
   - `channels:read`
3. Install app to workspace
4. Copy "Bot User OAuth Token"

#### Get Channel ID
1. Open Slack, right-click channel
2. Select "Copy link"
3. Extract ID from URL: `...channels/{CHANNEL_ID}`

#### Update .env
```env
SLACK_BOT_TOKEN=xoxb-...your-bot-token
SLACK_SIGNING_SECRET=...your-signing-secret
SLACK_CHANNEL_ID=C...your-channel-id
```

---

### 5. Salesforce Integration (Optional)

#### Create Connected App
1. Salesforce Setup → App Manager → New Connected App
2. Enable OAuth Settings
3. Selected OAuth Scopes:
   - Full access (full)
   - Perform requests at any time (refresh_token, offline_access)
4. Copy Consumer Key and Consumer Secret

#### Get Security Token
1. Salesforce → Settings → Reset Security Token
2. Check email for token

#### Update .env
```env
SALESFORCE_CLIENT_ID=...consumer-key
SALESFORCE_CLIENT_SECRET=...consumer-secret
SALESFORCE_USERNAME=your-email@company.com
SALESFORCE_PASSWORD=your-password
SALESFORCE_SECURITY_TOKEN=...security-token
```

---

### 6. Vector Database (Optional - Pinecone)

#### Setup Pinecone
1. Go to https://www.pinecone.io/
2. Create account and project
3. Create index: dimension=768, metric=cosine
4. Copy API key and environment

#### Update .env
```env
PINECONE_API_KEY=...your-api-key
PINECONE_ENVIRONMENT=...your-environment
```

---

### 7. JWT Secret

Generate a secure random string for JWT:

```powershell
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

Add to `.env`:
```env
JWT_SECRET=...your-generated-secret
```

---

## 🚀 Running the Application

### Using Docker Compose (Recommended)

```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **N8N Workflows**: http://localhost:5678
- **API Docs**: http://localhost:8000/docs

---

### Manual Setup (Development)

#### Backend
```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-extra.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```powershell
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

#### Celery Worker (Background Tasks)
```powershell
cd backend
celery -A src.services.celery_app worker --loglevel=info --pool=solo
```

#### Celery Beat (Scheduled Tasks)
```powershell
cd backend
celery -A src.services.celery_app beat --loglevel=info
```

---

## 🔌 N8N Workflow Setup

### Access N8N
1. Open http://localhost:5678
2. Login: admin / admin (default)

### Create Workflows

#### Workflow 1: Competitor Scraping
1. **HTTP Trigger** → Configure webhook
2. **Function Node** → Extract URL
3. **HTTP Request** → Call backend scraper API
4. **Slack Node** → Send notification

#### Workflow 2: News Monitoring
1. **Cron Node** → Schedule (every 4 hours)
2. **Perplexity API** → Search competitor news
3. **Function Node** → Process results
4. **HTTP Request** → Send to backend
5. **Slack Node** → Alert on high-impact news

---

## 🧪 Testing the Setup

### 1. Test Backend API
```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Register user
$body = @{
    email = "admin@vigilai.com"
    password = "admin123"
    full_name = "Admin User"
    role = "admin"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" -Method POST -Body $body -ContentType "application/json"
```

### 2. Test Frontend
1. Open http://localhost:3000
2. Login with created credentials
3. Navigate through dashboard

### 3. Add Test Competitor
Use the API or frontend to add a competitor:
```json
{
  "name": "Example Corp",
  "domain": "example.com",
  "pricing_url": "https://example.com/pricing",
  "careers_url": "https://example.com/careers",
  "blog_url": "https://example.com/blog"
}
```

### 4. Trigger Manual Scrape
```powershell
# Get token first (from login response)
$token = "your-jwt-token"
$headers = @{ Authorization = "Bearer $token" }

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/competitors/1/scrape" -Method POST -Headers $headers
```

---

## 📊 Chrome Extension Setup

### Load Extension
1. Open Chrome → Extensions → Developer mode ON
2. Click "Load unpacked"
3. Select `chrome-extension` folder
4. Extension icon appears in toolbar

### Configure Extension
1. Click extension icon
2. Login with VigilAI credentials (stored in chrome.storage)
3. Visit competitor website to see battlecard popup

---

## 🔒 Security Checklist

- [ ] Change default JWT_SECRET
- [ ] Use strong database passwords
- [ ] Enable HTTPS in production
- [ ] Restrict CORS origins
- [ ] Use environment-specific .env files
- [ ] Enable rate limiting on APIs
- [ ] Set up monitoring (Sentry)
- [ ] Regular backup of PostgreSQL database
- [ ] Rotate API keys periodically
- [ ] Use secrets management (AWS Secrets Manager, Azure Key Vault)

---

## 🐛 Troubleshooting

### Database Connection Error
```powershell
# Check PostgreSQL is running
docker ps | Select-String postgres

# View logs
docker logs vigilai_postgres
```

### Redis Connection Error
```powershell
# Check Redis is running
docker ps | Select-String redis

# Test connection
docker exec -it vigilai_redis redis-cli ping
```

### API Key Errors
- Verify keys are copied correctly without extra spaces
- Check API key quotas/limits
- Ensure billing is enabled (OpenAI, Anthropic)

### Frontend Build Errors
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules, .next
npm install
npm run build
```

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **Claude API**: https://docs.anthropic.com/
- **Notion API**: https://developers.notion.com/
- **Slack API**: https://api.slack.com/

---

## 🆘 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review API documentation: http://localhost:8000/docs
3. Check environment variables are set correctly

---

## 🎯 Next Steps

After setup is complete:
1. Add your first competitor
2. Trigger initial scrape
3. Set up N8N workflows for automation
4. Configure Slack notifications
5. Create Notion database for battlecards
6. Train LogBERT model on your logs
7. Set up monitoring and alerting

**Happy Intelligence Gathering! 🚀**
