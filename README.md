# VigilAI - Competitive Intelligence Platform

An enterprise-grade competitive intelligence platform that combines automated market surveillance with AIOps capabilities. It continuously monitors competitors, processes changes and delivers actionable insights to sales teams.

See [TECHNICAL_DOCS.md](./TECHNICAL_DOCS.md) for full architecture, API reference, and contributing guidelines.

---

## Key Features

- **Multi-Source Data Ingestion**: Web scraping, hiring signals, social media, and news monitoring
- **AI-Powered Analysis**: intelligent processing and insight generation
- **Dynamic Battlecards**: Auto-updated competitive battlecards synced to Notion
- **Real-Time Alerts**: Slack notifications for high-impact competitive changes
- **AIOps & Observability**: LogBERT-based anomaly detection and root cause analysis
- **Voice Assistant**: "Jarvis-like" voice control to query platform data and get spoken summaries
---

## �️ Tech Stack

### 🎨 Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.0.4 | React framework |
| **TypeScript** | 5.3.3 | Type safety |
| **TanStack React Query** | 5.13.4 | Data fetching |
| **Zustand** | 4.4.7 | State management |
| **Chart.js** | 4.5.1 | Data visualization |
| **Lucide React** | 0.294.0 | Icons |

### ⚙️ Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.104.1 | Web framework |
| **Uvicorn** | 0.24.0 | ASGI server |
| **Pydantic** | 2.5.0 | Data validation |
| **SQLAlchemy** | 2.0.23 | ORM |
| **Alembic** | 1.12.1 | Database migrations |
| **Celery** | 5.3.4 | Async task queue |

### 🗄️ Databases & Caching
| Technology | Version | Purpose |
|------------|---------|---------|
| **PostgreSQL** | 15 (Alpine) | Primary database |
| **Redis** | 7 (Alpine) | Caching & message broker |
| **ChromaDB** | 0.4.22 | Vector database |

### 🤖 AI/ML
| Technology | Version | Purpose |
|------------|---------|---------|
| **PyTorch** | 2.2.0 | ML framework |
| **Transformers** | 4.35.2 | NLP models (LogBERT) |
| **Sentence-Transformers** | 2.2.2 | Embeddings |
| **Google Gemini AI** | 0.3.2 | LLM integration |

### 🔧 Integrations
| Technology | Purpose |
|------------|---------|
| **Slack SDK** | Notifications |
| **Simple Salesforce** | CRM integration |
| **Notion Client** | Battlecard sync |
| **n8n** | Workflow automation |

### 🌐 Web Scraping
| Technology | Purpose |
|------------|---------|
| **BeautifulSoup4** | HTML parsing |
| **Playwright** | Browser automation |
| **Selenium** | Browser automation |
| **aiohttp** | HTTP clients |

### 🐳 Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker & Docker Compose** | Containerization |
| **Loguru** | Logging |
| **Sentry SDK** | Error monitoring |

---

## �🚀 Quick Start (How to Run)

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local tools)
- Node.js 18+ (for local frontend dev)

### 1. Clone and Setup

```powershell
# Clone repository
git clone https://github.com/yourusername/VigilAI.git
cd VigilAI

# Copy environment file
Copy-Item .env.example .env
```

**CRITICAL**: Edit `.env` and add your API keys. See [USER.md](./USER.md) for the setup wizard.

### 2. Start with Docker (Recommended)

```powershell
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 3. Access Applications

- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **N8N Automation**: [http://localhost:5678](http://localhost:5678)

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

**Built with ❤️ for smarter competitive intelligence**
