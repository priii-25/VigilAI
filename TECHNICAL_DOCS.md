# VigilAI - Technical Documentation

> **Version**: 2.0.0 | **Last Updated**: December 2024

## 📁 Project Structure

```
VigilAI/
├── backend/                          # FastAPI Backend (Python 3.12)
│   ├── src/
│   │   ├── api/                      # REST API Layer
│   │   │   └── v1/
│   │   │       ├── endpoints/        # Route handlers
│   │   │       │   ├── auth.py       # Authentication & JWT
│   │   │       │   ├── competitors.py # Competitor CRUD & scraping
│   │   │       │   ├── battlecards.py # Battlecard management
│   │   │       │   ├── logs.py       # Log analysis & anomalies
│   │   │       │   └── dashboard.py  # Dashboard metrics
│   │   │       └── router.py         # Route aggregation
│   │   │
│   │   ├── core/                     # Core Infrastructure (Production-Ready)
│   │   │   ├── config.py             # Pydantic settings management
│   │   │   ├── database.py           # Async SQLAlchemy engine
│   │   │   ├── redis.py              # Redis connection pool
│   │   │   ├── logging.py            # Structured JSON logging
│   │   │   ├── security.py           # JWT, password hashing
│   │   │   ├── rate_limiter.py       # Token bucket rate limiting
│   │   │   ├── circuit_breaker.py    # Circuit breaker pattern
│   │   │   ├── dead_letter_queue.py  # DLQ for failed tasks
│   │   │   ├── idempotency.py        # Idempotency key management
│   │   │   ├── backpressure.py       # Backpressure controller
│   │   │   └── request_context.py    # Request ID & tracing middleware
│   │   │
│   │   ├── models/                   # SQLAlchemy ORM Models
│   │   │   ├── base.py               # Base model class
│   │   │   ├── user.py               # User authentication
│   │   │   ├── competitor.py         # Competitor & CompetitorUpdate
│   │   │   ├── battlecard.py         # Battlecard & versions
│   │   │   ├── tenant.py             # Multi-tenancy support
│   │   │   └── log_anomaly.py        # Log anomaly tracking
│   │   │
│   │   ├── services/                 # Business Logic Layer
│   │   │   ├── ai/                   # AI/ML Processing
│   │   │   │   ├── processor.py      # Google Gemini integration
│   │   │   │   ├── prompt_registry.py # Version-controlled prompts
│   │   │   │   ├── change_detector.py # Content hash change detection
│   │   │   │   ├── logbert.py        # Log anomaly detection (BERT)
│   │   │   │   ├── anomaly_models.py # LSTM/Autoencoder models
│   │   │   │   ├── drift_detector.py # Concept drift detection
│   │   │   │   ├── chat_service.py   # AI chat interface
│   │   │   │   └── simulator.py      # Metric simulation
│   │   │   │
│   │   │   ├── integrations/         # External API Integrations
│   │   │   │   ├── slack_service.py      # Slack alerts (circuit-breaker protected)
│   │   │   │   ├── salesforce_service.py # CRM sync (OAuth2)
│   │   │   │   ├── notion_service.py     # Battlecard publishing
│   │   │   │   ├── email_service.py      # Email notifications
│   │   │   │   ├── google_news_service.py # News aggregation (free)
│   │   │   │   ├── perplexity_service.py # AI-powered research
│   │   │   │   ├── job_boards.py         # Greenhouse/Lever APIs
│   │   │   │   ├── reviews.py            # G2/Gartner scraping
│   │   │   │   └── vector_db.py          # ChromaDB embeddings
│   │   │   │
│   │   │   ├── scrapers/             # Web Scraping
│   │   │   │   └── web_scraper.py    # Pricing, careers, blog scrapers
│   │   │   ├── seo/                  # SEO Monitoring
│   │   │   │   └── seo_tracker.py    # Keyword ranking tracker
│   │   │   ├── social/               # Social Media
│   │   │   │   └── social_monitor.py # Twitter/LinkedIn monitoring
│   │   │   ├── battlecards/          # Battlecard Generation
│   │   │   │   └── generator.py      # AI-powered battlecard creation
│   │   │   ├── fallback_cache.py     # Graceful degradation cache
│   │   │   ├── websocket_service.py  # Real-time updates
│   │   │   ├── tasks/                # Background Jobs
│   │   │   │   └── scheduled_tasks.py # Celery scheduled tasks
│   │   │   ├── workflows/            # Business Workflows
│   │   │   │   └── approval_workflow.py # Human-in-the-loop
│   │   │   └── celery_app.py         # Celery configuration
│   │   │
│   │   └── main.py                   # FastAPI application entry
│   │
│   ├── tests/                        # Test Suite
│   │   ├── test_circuit_breaker.py   # Circuit breaker tests
│   │   └── test_dead_letter_queue.py # DLQ tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-extra.txt
│
├── frontend/                         # Next.js 14 Frontend
│   ├── src/
│   │   ├── components/               # React Components
│   │   │   ├── layout/               # Sidebar, Header
│   │   │   ├── dashboard/            # Dashboard widgets
│   │   │   ├── battlecards/          # Battlecard views
│   │   │   └── competitors/          # Competitor management
│   │   ├── lib/api.ts                # Axios API client
│   │   ├── pages/                    # Next.js pages
│   │   ├── store/authStore.ts        # Zustand state
│   │   └── styles/globals.css        # Tailwind CSS
│   ├── Dockerfile
│   └── package.json
│
├── chrome-extension/                 # Browser Extension
│   ├── manifest.json
│   ├── popup.html/js
│   ├── background.js
│   └── content.js
│
├── n8n/                              # Workflow Automation
│   └── vigilai_workflow.json         # Scheduled scraping workflow
│
├── docker-compose.yml                # Container orchestration
├── SETUP_WIZARD.md                   # Integration setup guide
├── TECHNICAL_DOCS.md                 # This file
└── .env.example                      # Environment template
```

---

## 🛠️ Technology Stack

### Backend Core
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Runtime |
| FastAPI | 0.104+ | Async web framework |
| SQLAlchemy | 2.0+ | Async ORM |
| PostgreSQL | 15+ | Primary database |
| Redis | 7+ | Caching, rate limiting, DLQ |
| Celery | 5.3+ | Distributed task queue |
| Pydantic | 2.0+ | Data validation |
| Loguru | 0.7+ | Structured logging |

### AI/ML Stack
| Technology | Purpose |
|------------|---------|
| Google Gemini 2.0 Flash | Primary LLM for analysis |
| PyTorch + Transformers | LogBERT anomaly detection |
| ChromaDB | Vector embeddings for RAG |
| Scikit-learn | Classical ML models |

### Frontend
| Technology | Purpose |
|------------|---------|
| Next.js 14 | React framework |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| TanStack Query | Data fetching |
| Zustand | State management |
| Recharts | Data visualization |

### External Integrations
| Service | Purpose | Auth Method |
|---------|---------|-------------|
| Slack | Real-time alerts | Bot Token |
| Salesforce | CRM sync | OAuth2 |
| Notion | Battlecard publishing | API Key |
| Google News | News aggregation | RSS (Free) |
| Greenhouse/Lever | Job tracking | Public API |

---

## 🏗️ System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA COLLECTION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Web Scrapers]  [Job Boards]  [News RSS]  [Social APIs]  [Review Sites]   │
│       ↓               ↓            ↓             ↓              ↓          │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ Change       │   │ AI Processor │   │ Impact       │   │ Noise        │ │
│  │ Detector     │ → │ (Gemini)     │ → │ Scorer       │ → │ Filter       │ │
│  │ (Content     │   │ + Circuit    │   │              │   │              │ │
│  │  Hashing)    │   │   Breaker    │   │              │   │              │ │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘ │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENCE LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ Battlecard   │   │ Trend        │   │ Human-in-   │   │ Version      │ │
│  │ Generator    │   │ Analysis     │   │ the-Loop    │   │ History      │ │
│  │              │   │              │   │ Review      │   │              │ │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘ │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DELIVERY LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│     [Slack]        [Notion]       [Salesforce]      [Email]      [WebSocket]│
│     Alerts        Battlecards      CRM Sync        Digests      Real-time   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow with Middleware

```
┌──────────┐   ┌──────────────────┐   ┌──────────────┐   ┌──────────────────┐
│  Client  │ → │ RequestContext   │ → │ Rate Limiter │ → │ Authentication   │
│          │   │ Middleware       │   │ (Token       │   │ (JWT)            │
│          │   │ (X-Request-ID,   │   │  Bucket)     │   │                  │
│          │   │  X-Correlation-ID│   │              │   │                  │
│          │   │  X-Tenant-ID)    │   │              │   │                  │
└──────────┘   └──────────────────┘   └──────────────┘   └──────────────────┘
                                                                    ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────────────┐
│ Route Handler    │ ← │ CircuitBreaker   │ ← │ Service Layer                │
│ (API Endpoint)   │   │ (External APIs)  │   │ (Business Logic)             │
└──────────────────┘   └──────────────────┘   └──────────────────────────────┘
```

---

## 🔧 Production-Ready Features

### 1. Circuit Breaker Pattern
**File**: `src/core/circuit_breaker.py`

Prevents cascading failures when external services are down.

```python
# Usage
@with_circuit_breaker("slack_api")
async def send_alert(message):
    await slack_client.post_message(message)

# Pre-configured breakers
CIRCUIT_BREAKERS = {
    "llm_api": ServiceCircuitBreaker("llm_api", failure_threshold=5, recovery_timeout=60),
    "slack_api": ServiceCircuitBreaker("slack_api", failure_threshold=3, recovery_timeout=60),
    "salesforce_api": ServiceCircuitBreaker("salesforce_api", failure_threshold=3, recovery_timeout=120),
    "notion_api": ServiceCircuitBreaker("notion_api", failure_threshold=3, recovery_timeout=60),
    "scraper": ServiceCircuitBreaker("scraper", failure_threshold=10, recovery_timeout=300),
}
```

**States**:
- `CLOSED`: Normal operation
- `OPEN`: Failing fast, no calls made
- `HALF_OPEN`: Testing if service recovered

### 2. Dead Letter Queue (DLQ)
**File**: `src/core/dead_letter_queue.py`

Handles failed background tasks with retry logic.

```python
# Automatic retry with exponential backoff
await dlq.add_failed_task(
    task_name="scrape_competitor",
    task_args={"competitor_id": 123},
    error=str(exception),
    retry_count=current_retry
)

# Retry delays: 60s → 300s → 900s → DLQ
RETRY_DELAYS = [60, 300, 900]
```

**Features**:
- Automatic retry scheduling
- Manual retry via API endpoint
- Statistics tracking
- Dead letter storage for debugging

### 3. Idempotency Keys
**File**: `src/core/idempotency.py`

Ensures safe request retries and prevents duplicate processing.

```python
@idempotent(key_generator=lambda req: f"scrape:{req.competitor_id}")
async def trigger_scrape(request):
    # This will only execute once per key within TTL
    pass
```

**Features**:
- Content hashing for deduplication
- Configurable TTL (default 24h)
- Redis-backed storage

### 4. Backpressure Controller
**File**: `src/core/backpressure.py`

Manages flow between producers and consumers to prevent overload.

```python
controller = BackpressureController(
    redis=redis_client,
    max_queue_size=1000,
    high_watermark=0.8,  # 80%
    low_watermark=0.3    # 30%
)

# Check before producing
if await controller.should_accept():
    await produce_task()
else:
    await controller.wait_for_capacity(timeout=30)
```

### 5. Request Context & Tracing
**File**: `src/core/request_context.py`

Provides structured logging context across the request lifecycle.

```python
# Automatic headers propagation
X-Request-ID: uuid
X-Correlation-ID: uuid (from client or generated)
X-Tenant-ID: tenant identifier

# Structured log output includes:
{
    "timestamp": "2024-12-28T02:30:00Z",
    "level": "INFO",
    "message": "Competitor scraped",
    "request_id": "abc-123",
    "correlation_id": "xyz-789",
    "tenant_id": "tenant_1"
}
```

### 6. Graceful Degradation
**File**: `src/services/fallback_cache.py`

Serves stale data when live services fail.

```python
cache = FallbackCache(redis_client)

# Get with fallback
result = await cache.get_or_fetch(
    key="battlecard:123",
    fetch_fn=lambda: fetch_fresh_battlecard(123),
    ttl=3600,
    stale_ttl=86400  # Serve stale for 24h if fresh fetch fails
)
```

---

## 🤖 AI/LLM Integration

### Prompt Registry
**File**: `src/services/ai/prompt_registry.py`

Version-controlled prompt templates with A/B testing support.

```python
# Registered prompts
prompts = [
    "analyze_pricing",          # Pricing change analysis
    "generate_battlecard_section",  # Battlecard generation
    "detect_noise",             # Spam/noise filtering
    "analyze_hiring",           # Hiring trend analysis
    "summarize_content",        # Content summarization
    "generate_objection_handling",  # Sales objections
    "generate_positioning",     # Market positioning
]

# Each prompt includes:
PromptTemplate(
    name="analyze_pricing",
    version="1.0.0",
    template="...",
    parameters=["competitor_name", "pricing_data"],
    ai_settings={"temperature": 0.3, "max_tokens": 1000}
)
```

### Change Detection
**File**: `src/services/ai/change_detector.py`

Only triggers AI processing when content actually changes.

```python
detector = ChangeDetector(redis_client)

if await detector.has_changed("competitor:123:pricing", new_content):
    # Content changed, run expensive AI analysis
    analysis = await ai_processor.analyze(new_content)
```

### AI Processor
**File**: `src/services/ai/processor.py`

Google Gemini integration with circuit breaker protection.

```python
class AIProcessor:
    @with_circuit_breaker("llm_api")
    async def analyze_pricing_changes(self, pricing_data: dict) -> dict:
        prompt = self.prompt_registry.get("analyze_pricing")
        response = await self._call_gemini(prompt.render(pricing_data))
        return self._parse_json_response(response)

    # Available methods:
    # - analyze_pricing_changes()
    # - analyze_hiring_trends()
    # - generate_battlecard_section()
    # - summarize_content_change()
    # - detect_noise()
```

---

## 🔌 External Integrations

### Slack Integration
**File**: `src/services/integrations/slack_service.py`

Circuit breaker protected Slack notifications.

```python
slack = SlackService()

# Test endpoint: GET /system/slack/test
# Send test: POST /system/slack/send-test

# Alert types:
await slack.send_competitor_alert(update)  # High-impact alerts
await slack.send_incident_alert(incident)  # System incidents
await slack.send_weekly_digest(digest)     # Weekly summary
```

**Alert Triggers**:
- Impact score ≥ 7.0
- Category in ['acquisition', 'funding', 'pricing']

### Salesforce Integration
**File**: `src/services/integrations/salesforce_service.py`

OAuth2-authenticated CRM sync.

```python
sf = SalesforceService()

# Test endpoint: GET /system/salesforce/test

# Available operations:
sf.push_kill_points_to_opportunity(opp_id, competitor, kill_points)
sf.find_opportunities_by_competitor(competitor_name)
sf.auto_enrich_relevant_opportunities(competitor, battlecard)
```

**Authentication**: OAuth2 Password Grant (not SOAP API)

### Notion Integration
**File**: `src/services/integrations/notion_service.py`

Battlecard publishing to Notion databases.

```python
notion = NotionService()
await notion.publish_battlecard(battlecard)
await notion.update_battlecard(battlecard_id, updates)
```

---

## 📊 Database Models

### Multi-Tenancy Support
**File**: `src/models/tenant.py`

Row-level isolation for multi-tenant deployments.

```python
class Tenant(Base):
    id: int
    name: str
    slug: str  # Unique identifier
    settings: TenantSettings  # Feature flags, limits
    subscription_tier: str  # free, pro, enterprise

class TenantMixin:
    tenant_id: int  # All tenant-aware models inherit this
```

### Competitor Model
**File**: `src/models/competitor.py`

```python
class Competitor(Base):
    id: int
    tenant_id: int  # Multi-tenancy
    name: str
    domain: str
    pricing_url: str
    careers_url: str
    blog_url: str
    content_hash: str  # For change detection
    extra_data: JSON  # Twitter handle, etc.

class CompetitorUpdate(Base):
    id: int
    tenant_id: int
    competitor_id: int
    update_type: str  # pricing, hiring, news, content
    category: str     # funding, acquisition, product
    title: str
    summary: str
    impact_score: float
    content_hash: str
    previous_hash: str
    is_noise: bool
    idempotency_key: str
    raw_data: JSON

class CompetitorSnapshot(Base):
    # Immutable point-in-time snapshot for temporal modeling
```

### Battlecard Model
**File**: `src/models/battlecard.py`

```python
class Battlecard(Base):
    id: int
    tenant_id: int
    competitor_id: int
    version: int
    overview: str
    strengths: JSON
    weaknesses: JSON
    key_differentiators: JSON
    objection_handling: JSON
    pricing_comparison: JSON
    customer_stories: JSON
    
    # Human-in-the-loop fields
    review_status: str  # pending, approved, rejected
    reviewed_by: int
    review_notes: str
    ai_confidence: float
    
    # AI generation metadata
    ai_model_version: str
    prompt_version: str

class BattlecardVersion(Base):
    # Full version history

class BattlecardSection(Base):
    # Granular section updates
```

---

## 📡 API Reference

### System Endpoints

```bash
# Health checks
GET  /health                    # Basic health
GET  /health/detailed           # Detailed with dependencies

# System monitoring
GET  /system/circuit-breakers   # Circuit breaker states
POST /system/circuit-breakers/reset  # Reset all breakers
GET  /system/dlq                # Dead letter queue status
POST /system/dlq/{task_id}/retry    # Retry dead letter

# Integration tests
GET  /system/slack/test         # Test Slack connection
POST /system/slack/send-test    # Send test Slack message
GET  /system/salesforce/test    # Test Salesforce connection
```

### Authentication

```bash
POST /api/v1/auth/register      # Create account
POST /api/v1/auth/login         # Get JWT token
GET  /api/v1/auth/me            # Get current user
```

### Competitors

```bash
GET    /api/v1/competitors/              # List all
POST   /api/v1/competitors/              # Create new
GET    /api/v1/competitors/{id}          # Get details
PUT    /api/v1/competitors/{id}          # Update
DELETE /api/v1/competitors/{id}          # Delete
POST   /api/v1/competitors/{id}/scrape   # Trigger scrape
GET    /api/v1/competitors/{id}/updates  # Get updates
GET    /api/v1/competitors/{id}/news     # Get live news
```

### Battlecards

```bash
GET    /api/v1/battlecards/                    # List all
GET    /api/v1/battlecards/{id}                # Get details
GET    /api/v1/battlecards/competitor/{id}     # By competitor
POST   /api/v1/battlecards/{id}/publish        # Publish to Notion
POST   /api/v1/battlecards/{id}/approve        # Approve for use
POST   /api/v1/battlecards/{id}/reject         # Reject with feedback
```

### Log Analysis (AIOps)

```bash
POST   /api/v1/logs/analyze              # Analyze log batch
GET    /api/v1/logs/anomalies            # List anomalies
GET    /api/v1/logs/incidents            # List incidents
POST   /api/v1/logs/incidents/{id}/resolve  # Resolve incident
GET    /api/v1/logs/root-cause/{id}      # Root cause analysis
```

### Dashboard

```bash
GET    /api/v1/dashboard/stats           # Key metrics
GET    /api/v1/dashboard/recent-activity # Activity feed
GET    /api/v1/dashboard/competitor-radar # Real-time alerts
```

---

## 🔐 Security

### Authentication
- **JWT Tokens**: RS256 signed, 24h expiry
- **Password Hashing**: bcrypt with salt
- **Token Refresh**: Automatic refresh mechanism

### Rate Limiting
```python
# Token bucket algorithm
RateLimiter(
    redis=redis_client,
    max_tokens=100,      # Per minute
    refill_rate=1.67     # Tokens per second
)
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Security
- All secrets via environment variables
- `.env` files in `.gitignore`
- Production: Use secret managers (AWS Secrets, Vault)

---

## 📈 Performance Optimizations

| Feature | Implementation | Benefit |
|---------|----------------|---------|
| Async/Await | Throughout codebase | Non-blocking I/O |
| Connection Pooling | SQLAlchemy + asyncpg | Efficient DB usage |
| Redis Caching | Multi-layer caching | Sub-10ms reads |
| Background Tasks | Celery workers | Offload heavy work |
| Circuit Breakers | Fail-fast on errors | Prevent cascading |
| Content Hashing | Change detection | Skip redundant AI |
| Backpressure | Queue management | Prevent overload |

---

## 🧪 Testing

### Run Tests
```bash
cd backend

# Core system tests
python -m pytest tests/test_circuit_breaker.py tests/test_dead_letter_queue.py -v

# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Categories
- **Unit Tests**: Core modules (circuit breaker, DLQ, idempotency)
- **Integration Tests**: API endpoints, database operations
- **Mock Tests**: External API integrations

---

## 🚀 Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

**Services**:
| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5434 | Database |
| redis | 6379 | Cache/broker |
| backend | 8000 | API server |
| frontend | 3000 | Web UI |
| celery_worker | - | Background tasks |
| n8n | 5678 | Workflow automation |

### Environment Variables

```env
# Required
DATABASE_URL=postgresql+asyncpg://vigilai:password@localhost:5434/vigilai
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
GOOGLE_API_KEY=your-gemini-key

# Integrations (Optional)
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C...
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
SALESFORCE_USERNAME=...
SALESFORCE_PASSWORD=...
SALESFORCE_SECURITY_TOKEN=...
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=...

# Production
APP_ENV=production
SENTRY_DSN=...
```

---

## 📊 Observability

### Structured Logging
```python
# Production JSON format
{
    "timestamp": "2024-12-28T02:30:00.123Z",
    "level": "INFO",
    "message": "Competitor scraped",
    "request_id": "abc-123",
    "correlation_id": "xyz-789",
    "tenant_id": "tenant_1",
    "extra": {"competitor_id": 42}
}
```

### Log Files
```
logs/
├── vigilai_2024-12-28.log      # All logs
├── vigilai_2024-12-28.json     # Structured (production)
└── errors_2024-12-28.log       # Errors only
```

### Monitoring Endpoints
| Endpoint | Purpose |
|----------|---------|
| `/health` | Liveness probe |
| `/health/detailed` | Readiness probe |
| `/system/circuit-breakers` | Service health |
| `/system/dlq` | Failed task tracking |

---

## 🔄 Workflow Automation (N8N)

### Default Workflow
**File**: `n8n/vigilai_workflow.json`

```
Schedule (9 AM daily)
    ↓
Fetch all competitors
    ↓
For each competitor:
    ↓
Trigger deep scrape via API
    ↓
Wait for completion
    ↓
If high-impact updates found:
    ↓
Send Slack alert
```

---

## 📝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `python -m pytest tests/ -v`
5. Commit with conventional commits: `git commit -m "feat: add amazing feature"`
6. Push and open Pull Request

### Code Style
- Python: Black formatter, Ruff linter
- TypeScript: ESLint + Prettier
- Commit messages: Conventional Commits

---

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built for competitive intelligence automation
- Powered by Google Gemini 2.0 Flash
- Inspired by enterprise system design patterns
- Designed for sales and product teams

---

**Repository**: https://github.com/priii-25/VigilAI
