# VigilAI - Competitive Intelligence Platform

![VigilAI Banner](https://via.placeholder.com/1200x300/667eea/ffffff?text=VigilAI+-+Competitive+Intelligence+Platform)

## 🎯 Overview

VigilAI (Sentinel-CI) is a production-ready, enterprise-grade competitive intelligence platform that combines automated market surveillance with AIOps capabilities. It continuously monitors competitors, processes changes using LLMs, and delivers actionable insights to sales teams.

See [TECHNICAL_DOCS.md](./TECHNICAL_DOCS.md) for full architecture, API reference, and contributing guidelines.

---

## ✨ Key Features

- **🔍 Multi-Source Data Ingestion**: Web scraping, hiring signals, social media, and news monitoring
- **🤖 AI-Powered Analysis**: Claude/GPT-4 for intelligent processing and insight generation
- **📊 Dynamic Battlecards**: Auto-updated competitive battlecards synced to Notion
- **🔔 Real-Time Alerts**: Slack notifications for high-impact competitive changes
- **🛡️ AIOps & Observability**: LogBERT-based anomaly detection and root cause analysis
- **🎙️ Voice Assistant**: "Jarvis-like" voice control to query platform data and get spoken summaries
- **🌐 Chrome Extension**: Battlecard companion for on-the-go competitive intelligence
- **⚡ Production-Ready**: Docker, async processing, caching, and scalability built-in

---

## 🚀 Quick Start (How to Run)

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
