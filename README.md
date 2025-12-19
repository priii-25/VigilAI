# VigilAI - Competitive Intelligence Platform

![VigilAI Banner](https://via.placeholder.com/1200x300/667eea/ffffff?text=VigilAI+-+Competitive+Intelligence+Platform)

## 🎯 Overview

VigilAI (Sentinel-CI) is a production-ready, enterprise-grade competitive intelligence platform that combines automated market surveillance with AIOps capabilities. It continuously monitors competitors, processes changes using LLMs, and delivers actionable insights to sales teams.

### Key Features

- **🔍 Multi-Source Data Ingestion**: Web scraping, hiring signals, social media, and news monitoring
- **🤖 AI-Powered Analysis**: Claude/GPT-4 for intelligent processing and insight generation
- **📊 Dynamic Battlecards**: Auto-updated competitive battlecards synced to Notion
- **🔔 Real-Time Alerts**: Slack notifications for high-impact competitive changes
- **🛡️ AIOps & Observability**: LogBERT-based anomaly detection and root cause analysis
- **🎙️ Voice Assistant**: "Jarvis-like" voice control to query platform data and get spoken summaries
- **🌐 Chrome Extension**: Battlecard companion for on-the-go competitive intelligence
- **⚡ Production-Ready**: Docker, async processing, caching, and scalability built-in

---

## 📁 Project Structure

```
VigilAI/
├── backend/                     # FastAPI Backend
│   ├── src/
│   │   ├── api/                # API endpoints
│   │   │   └── v1/
│   │   │       ├── endpoints/  # Route handlers
│   │   │       │   ├── auth.py
│   │   │       │   ├── competitors.py
│   │   │       │   ├── battlecards.py
│   │   │       │   ├── logs.py
│   │   │       │   └── dashboard.py
│   │   │       └── router.py
│   │   ├── core/               # Core functionality
│   │   │   ├── config.py       # Settings management
│   │   │   ├── database.py     # Database connection
│   │   │   ├── redis.py        # Cache manager
│   │   │   ├── logging.py      # Logging setup
│   │   │   └── security.py     # Auth & JWT
│   │   ├── models/             # Database models
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── competitor.py
│   │   │   ├── battlecard.py
│   │   │   └── log_anomaly.py
│   │   ├── services/           # Business logic
│   │   │   ├── scrapers/
│   │   │   │   └── web_scraper.py
│   │   │   ├── ai/
│   │   │   │   ├── processor.py    # AI analysis
│   │   │   │   └── logbert.py      # Log anomaly detection
│   │   │   ├── integrations/
│   │   │   │   ├── slack_service.py
│   │   │   │   └── notion_service.py
│   │   │   ├── tasks/
│   │   │   │   └── scheduled_tasks.py
│   │   │   └── celery_app.py
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-extra.txt
│
├── frontend/                    # Next.js Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Header.tsx
│   │   │   └── dashboard/
│   │   │       ├── DashboardStats.tsx
│   │   │       └── RecentActivity.tsx
│   │   ├── lib/
│   │   │   └── api.ts          # API client
│   │   ├── pages/
│   │   │   ├── _app.tsx
│   │   │   ├── index.tsx       # Dashboard
│   │   │   └── login.tsx
│   │   ├── store/
│   │   │   └── authStore.ts
│   │   └── styles/
│   │       └── globals.css
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── next.config.js
│
├── chrome-extension/            # Chrome Extension
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   ├── background.js
│   └── content.js
│
├── docker-compose.yml           # Container orchestration
├── .env.example                 # Environment template
├── .gitignore
├── requirements.txt             # Python dependencies
├── package.json                 # Node dependencies
└── USER.md                      # Setup guide
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. Clone and Setup

```powershell
# Clone repository
git clone https://github.com/yourusername/VigilAI.git
cd VigilAI

# Copy environment file
Copy-Item .env.example .env

# Edit .env and add your API keys (see USER.md)
```

### 2. Start with Docker

```powershell
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **N8N Workflows**: http://localhost:5678

---

## 🎮 Usage Guide

### 🎙️ Using the Voice Assistant
1.  Look for the **Microphone Icon 🎙️** in the bottom-right corner of any page.
2.  Click to activate.
3.  **Ask a question**:
    *   *"What is the status of Competitor X?"*
    *   *"Summarize the latest market news."*
    *   *"Are there any system errors?"*
4.  VigilAI will speak the answer back to you using the platform's aggregated data!

### 📊 Monitoring Competitors
1.  Go to the **Competitors** page.
2.  Add a competitor (Domain + Name).
3.  Click **Scrape** to fetch initial data.
4.  View generated **Battlecards** to see Strengths, Weaknesses, and Kill Points.

### 🔔 Receiving Alerts
- Ensure you have configured Slack in `.env`.
- You will receive notifications in `#competitive-intel` when:
    - A competitor changes pricing.
    - A new blog post is published.
    - A serious system anomaly occurs.

---

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern async Python web framework
- **SQLAlchemy**: ORM with async support
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker
- **Celery**: Distributed task queue
- **PyTorch + Transformers**: LogBERT implementation
- **Beautiful Soup**: Web scraping
- **Anthropic Claude**: AI analysis
- **OpenAI GPT-4**: Alternative AI processing

### Frontend
- **Next.js 14**: React framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **TanStack Query**: Data fetching
- **Zustand**: State management
- **Axios**: HTTP client

### Integrations
- **Notion API**: Battlecard publishing
- **Slack API**: Real-time notifications
- **Perplexity API**: News aggregation
- **Salesforce API**: CRM integration (optional)

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **N8N**: Workflow automation
- **Nginx**: Reverse proxy (production)

---

## 📊 Architecture

### Data Flow

```
[Web Scrapers] → [Redis Queue] → [AI Processor] → [PostgreSQL]
                                        ↓
                                   [Analysis]
                                        ↓
                     ┌──────────────────┼──────────────────┐
                     ↓                  ↓                  ↓
              [Notion API]      [Slack API]       [Vector DB]
              (Battlecards)     (Alerts)          (RAG Cache)
```

### Components

1. **Data Collection Layer**
   - Web scrapers (pricing, careers, blogs)
   - API integrations (news, reviews)
   - Scheduled monitoring (Celery)

2. **Processing Layer**
   - Change detection and diff analysis
   - AI-powered summarization
   - Impact scoring
   - Noise filtering

3. **Intelligence Layer**
   - Battlecard generation
   - Trend analysis
   - Competitive insights

4. **Delivery Layer**
   - Real-time Slack notifications
   - Notion database updates
   - Chrome extension popup

5. **Observability Layer**
   - LogBERT anomaly detection
   - Root cause analysis
   - Incident management

---

## 🔑 Key Features Explained

### 1. Automated Web Scraping
- **Smart Detection**: HEAD requests check `Last-Modified` before full scrape
- **Proxy Support**: Built-in proxy rotation for reliability
- **Multi-Target**: Pricing, careers, and content pages
- **Noise Filtering**: AI determines substantive vs cosmetic changes

### 2. AI-Powered Analysis
- **Impact Scoring**: 0-10 scale for prioritizing insights
- **Strategic Analysis**: Hiring trends reveal product direction
- **Objection Handling**: Auto-generates sales talking points
- **Battlecard Generation**: Creates comprehensive competitive profiles

### 3. LogBERT Anomaly Detection
- **Log Parsing**: Structured log analysis
- **Pattern Recognition**: BERT-based sequence modeling
- **Anomaly Scoring**: Threshold-based detection
- **Root Cause Analysis**: AI explains incidents

### 4. Real-Time Distribution
- **Slack Alerts**: Formatted messages with action buttons
- **Notion Sync**: Live battlecard updates
- **Chrome Extension**: Battlecards on competitor sites
- **Weekly Digests**: Executive summaries

---

## 📖 API Documentation

### Authentication

```bash
POST /api/v1/auth/register
POST /api/v1/auth/login
```

### Competitors

```bash
GET    /api/v1/competitors/           # List all
POST   /api/v1/competitors/           # Create new
GET    /api/v1/competitors/{id}       # Get details
POST   /api/v1/competitors/{id}/scrape # Trigger scrape
```

### Battlecards

```bash
GET    /api/v1/battlecards/                    # List all
GET    /api/v1/battlecards/{id}                # Get details
GET    /api/v1/battlecards/competitor/{id}     # By competitor
POST   /api/v1/battlecards/{id}/publish        # Publish
```

### Log Analysis

```bash
POST   /api/v1/logs/analyze              # Analyze logs
GET    /api/v1/logs/anomalies            # List anomalies
GET    /api/v1/logs/incidents            # List incidents
POST   /api/v1/logs/incidents/{id}/resolve # Resolve incident
```

### Dashboard

```bash
GET    /api/v1/dashboard/stats           # Key metrics
GET    /api/v1/dashboard/recent-activity # Activity feed
```

---

## 🎨 Frontend Pages

- **Dashboard**: Overview with stats and activity feed
- **Competitors**: Manage tracked competitors
- **Battlecards**: View and manage battlecards
- **Log Analysis**: System health and anomalies
- **Analytics**: Trends and insights (to be implemented)

---

## 🔧 Configuration

See **USER.md** for detailed setup instructions including:
- API key configuration
- Notion integration
- Slack bot setup
- Salesforce connection
- Database configuration
- Security settings

---

## 🧪 Development

### Backend Development

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.main:app --reload
```

### Frontend Development

```powershell
cd frontend
npm install
npm run dev
```

### Run Tests

```powershell
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

---

## 📦 Deployment

### Production Docker Build

```powershell
# Build images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Key production settings:
- `APP_ENV=production`
- `DATABASE_URL=postgresql://...`
- `REDIS_URL=redis://...`
- `FRONTEND_URL=https://vigilai.com`
- `SENTRY_DSN=...` (error tracking)

---

## 🔐 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Rate limiting (to be implemented)
- Environment variable secrets
- HTTPS enforced in production

---

## 📈 Performance

- **Async/Await**: Non-blocking I/O throughout
- **Redis Caching**: Sub-10ms battlecard retrieval
- **Connection Pooling**: Efficient database usage
- **Background Tasks**: Celery for async operations
- **Vector Database**: RAG for fast context retrieval

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Built for competitive intelligence automation
- Inspired by modern AIOps practices
- Powered by Claude, GPT-4, and BERT
- Designed for sales and product teams

---

## 📞 Contact

For support or questions, please open an issue or contact the development team.

**Built with ❤️ for smarter competitive intelligence**
