# VigilAI - Technical Documentation

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

## 📖 API Reference

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

## 🎨 Frontend Structure

- **Dashboard**: Overview with stats and activity feed
- **Competitors**: Manage tracked competitors
- **Battlecards**: View and manage battlecards
- **Log Analysis**: System health and anomalies
- **Analytics**: Trends and insights (to be implemented)

---

## 🔧 Deployment & Configuration

### Environment Variables

Key production settings:
- `APP_ENV=production`
- `DATABASE_URL=postgresql://...`
- `REDIS_URL=redis://...`
- `FRONTEND_URL=https://vigilai.com`
- `SENTRY_DSN=...` (error tracking)

### Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Rate limiting (to be implemented)
- Environment variable secrets
- HTTPS enforced in production

### Performance

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

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built for competitive intelligence automation
- Inspired by modern AIOps practices
- Powered by Claude, GPT-4, and BERT
- Designed for sales and product teams

## 📞 Contact

For support or questions, please open an issue or contact the development team.
