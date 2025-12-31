# VigilAI n8n Workflows

Automation workflows for competitive intelligence monitoring and incident management.

## Available Workflows

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `complete_data_collection.json` | 4x daily + webhook | **Full data collection** across ALL sources (Pricing, News, Social, Jobs, Reviews, SEO) |
| `competitor_monitoring.json` | Schedule: 9 AM, 2 PM, 6 PM | Scrapes competitors, routes alerts by impact score |
| `battlecard_automation.json` | Webhook | Auto-creates/updates battlecards, syncs to Notion & Salesforce |
| `weekly_digest.json` | Monday 8 AM | Weekly intelligence summary via Slack + Email |
| `aiops_incidents.json` | Webhook | Anomaly detection → AI root cause → severity routing |

## Quick Start

### 1. Start n8n
```bash
docker-compose up -d n8n
```

### 2. Access n8n UI
Open [http://localhost:5678](http://localhost:5678)

### 3. Import Workflows
1. Go to **Workflows** → **Import from File**
2. Select each `.json` file from this directory
3. Activate the workflows

## Required Credentials

Configure these in n8n Settings → Credentials:

| Credential | Used By | Setup |
|------------|---------|-------|
| **Slack API** | All workflows | Create Slack App with `chat:write` scope |
| **SMTP** | Weekly Digest | Email server settings |

### Backend API Credentials

Configure these in your `.env` file for enhanced data collection:

#### Social Media APIs (Optional but Recommended)

| Variable | Purpose | How to Get |
|----------|---------|------------|
| `TWITTER_BEARER_TOKEN` | Twitter/X monitoring | [developer.twitter.com](https://developer.twitter.com/en/portal/dashboard) → Create App → Bearer Token |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn company posts | [linkedin.com/developers](https://www.linkedin.com/developers/apps) → Create App → OAuth 2.0 |

**Note:** Without these tokens, social monitoring falls back to Google News RSS (still functional but less comprehensive).

#### Review Data APIs (Optional)

| Variable | Purpose | How to Get |
|----------|---------|------------|
| `SERPAPI_KEY` | G2/Gartner review snippets | [serpapi.com](https://serpapi.com) → 100 free searches/month |

**Note:** Without SerpAPI, the system uses Capterra scraping and Google News as fallbacks.

## Slack Channels Required

Create these channels in your Slack workspace:

- `#competitive-intel` - General updates
- `#competitive-intel-urgent` - High-impact alerts (score ≥ 7)
- `#vigilai-alerts` - System/API errors
- `#vigilai-incidents` - AIOps alerts

## Webhook Endpoints

After importing, these webhooks will be available:

| Webhook | Path | Purpose |
|---------|------|---------|
| Battlecard Trigger | `/webhook/battlecard-trigger` | Triggers battlecard workflow |
| Anomaly Detected | `/webhook/anomaly-detected` | Triggers AIOps incident flow |

### Example Webhook Payload

**Battlecard Trigger:**
```json
{
  "competitor_id": 1,
  "competitor_name": "Acme Corp",
  "update_type": "pricing",
  "impact_score": 8,
  "summary": "20% price reduction on Enterprise tier"
}
```

**Anomaly Detected:**
```json
{
  "log_message": "Connection timeout to database",
  "anomaly_score": 0.85,
  "log_source": "api-server"
}
```

## Customization

### Change Schedule Times
Edit `competitor_monitoring.json` → `Schedule (3x Daily)` node → modify `triggerAtHour` values.

### Change Impact Threshold
Edit the `Categorize by Impact` code node → change `if (update.impact_score >= 7)` to desired threshold.

### Add More Channels
Duplicate Slack nodes and update channel names.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        n8n Workflows                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────────┐    ┌──────────────────┐             │
│   │   Competitor     │    │   Battlecard     │             │
│   │   Monitoring     │    │   Automation     │             │
│   │   (Scheduled)    │    │   (Webhook)      │             │
│   └────────┬─────────┘    └────────┬─────────┘             │
│            │                       │                        │
│            ▼                       ▼                        │
│   ┌──────────────────────────────────────────┐             │
│   │            VigilAI Backend API           │             │
│   │         http://backend:8000              │             │
│   └──────────────────────────────────────────┘             │
│            │                       │                        │
│            ▼                       ▼                        │
│   ┌──────────────────┐    ┌──────────────────┐             │
│   │      Slack       │    │   Salesforce     │             │
│   │                  │    │   Notion         │             │
│   └──────────────────┘    └──────────────────┘             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Workflows not triggering
1. Ensure workflows are **Active** (toggle in n8n)
2. Check Docker network: backend should be reachable at `http://backend:8000`

### Slack notifications failing
1. Verify Slack credentials in n8n
2. Ensure bot is invited to channels
3. Check Slack App has `chat:write` permission

### API errors
Run the health check:
```bash
python tools/check_n8n.py
```
