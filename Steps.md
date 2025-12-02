***

# Project: CompetitIV (Competitive Intelligence Velocity)
### *Automated Market Surveillance & Dynamic Sales Enablement Engine*

---

## 1. Executive Summary
**The Problem:** In fast-paced markets, sales teams lose deals because they rely on static, outdated competitive spreadsheets. Product Marketing Managers (PMMs) cannot manually track 20+ competitors across web changes, hiring trends, and pricing updates while maintaining fresh "Battlecards" for sales.

**The Solution:** VigilAI is an autonomous intelligence agent. It continuously monitors the competitive landscape using multi-source data ingestion, processes changes using LLMs to determine business impact, and auto-updates Battlecards in real-time. It delivers actionable insights directly to the Sales team via Slack and CRM, increasing win rates and reducing research time by 90%.

---

## 2. Feature List

### A. Omni-Channel Data Ingestion
*   **Web Surveillance:** Tracks competitor pricing pages, homepage pivots, and new product pages (using sitemap monitoring).
*   **Hiring Signals:** Monitors Greenhouse/Lever APIs to detect strategic pivots (e.g., a competitor hiring "React Native Engineers" implies a mobile app launch).
*   **Social & Sentiment:** Aggregates G2/Gartner reviews and LinkedIn announcements to gauge market sentiment and feature gaps.
*   **SEO & Content Radar:** Tracks keyword ranking shifts to understand competitor go-to-market strategies.

### B. Intelligent Processing Core
*   **Noise Filtering & Change Detection:** Uses diff-algorithms to ignore minor HTML changes and focus on substantive content updates.
*   **Contextual Summarization:** LLMs (Claude/GPT-4) analyze the *implication* of a change (e.g., "Competitor dropped pricing by 10%" -> "Price War Alert: Prepare value-based objection handling").
*   **Tagging & Categorization:** Auto-sorts intel into Pricing, Feature Release, Leadership Change, or Partnership.

### C. Dynamic Battlecard Generation
*   **Live Battlecards:** Notion-based dashboards that update instantly when new intel is verified.
*   **Objection Handling Generator:** Synthesizes "Why we win" scripts based on specific competitor weaknesses found in recent reviews.
*   **Personalization Engine:** Generates specific talking points based on the prospect's industry (e.g., "If pitching to Healthcare, mention Competitor X lacks HIPAA compliance").

### D. Active Distribution
*   **CRM Enrichment:** Pushes "Kill Points" directly into Salesforce Opportunity records.
*   **Slack "News Flash":** Real-time alerts for high-priority events (e.g., Funding rounds, Acquisition news).
*   **Weekly Digests:** Automated summaries for the executive leadership team.

---

## 4. Scalability & Production Engineering
*To make this a "real-world" product, the following engineering principles are applied:*

### A. Low Latency & Optimization
*   **Incremental Scraping:** Instead of scraping full sites daily, we check `Last-Modified` headers and Sitemaps first. We only process pages that have changed, saving compute resources and reducing latency.
*   **Asynchronous Processing:** Data collection is decoupled from analysis. A message queue (built into N8N or external Redis) buffers incoming web data so the LLM processing pipeline doesn't bottleneck during high-traffic updates.
*   **Vector Caching:** We implement RAG (Retrieval Augmented Generation). Historic competitor data is chunked and embedded. When generating a battlecard, the LLM retrieves only relevant context rather than reprocessing the entire database, reducing token costs and latency.

### B. Handling "Data Noise" & Reliability
*   **Proxy Rotation:** To prevent IP bans from competitor sites, the scraping engine utilizes a rotating proxy network.
*   **Hallucination Guardrails:**
    *   *Verification Step:* Every LLM-generated insight requires a source URL citation.
    *   *Human-in-the-Loop:* "High Impact" alerts (e.g., pricing changes >20%) are routed to a PMM for one-click approval in Slack before global distribution.
*   **Schema Standardization:** Regardless of source (G2, Twitter, Website), all data is normalized into a standard JSON schema (Event, Date, Impact Score, Source) before storage.

### C. Enterprise Security
*   **RBAC (Role-Based Access Control):** Ensuring only Admin PMMs can edit core positioning, while Sales reps have "Read-Only" access to Battlecards.
*   **Data Sanitization:** Stripping PII (Personally Identifiable Information) from scraped reviews before feeding them into public LLM APIs.

---

## 5. Dataset Strategy
*Using a hybrid approach of static historical data and dynamic live data.*

### 1. Static Backfill (Historical Context)
*Used to train the categorization model and populate initial baselines.*
*   **eCommerce-dataset-samples (GitHub):** For pricing history modeling.
*   **Pricing Strategy Dataset (Kaggle):** To teach the LLM how to identify pricing tiers.

### 2. Dynamic Collection (Live)
*   **Web Scraping Targets:** Competitor pricing pages, "About Us" pages, and "Careers" pages.
*   **Synthetic Data Generation:** For the competition demo, we will simulate a "Competitor Press Release" to demonstrate the real-time alert pipeline instantly.

---

## 6. Success Metrics & KPIs

| Metric | Target | How it is measured |
| :--- | :--- | :--- |
| **Data Freshness** | < 4 Hours | Time from competitor website update to Battlecard reflection. |
| **Accuracy** | 95% | Feedback loop: Sales reps verify insights via "Thumbs up/down" in Slack. |
| **Sales Efficiency** | 10x Faster | Reduction in time spent by Reps searching for "How do I beat Competitor X?" |
| **Win Rate** | +15% | Correlation between "Battlecard Views" in Salesforce and "Closed-Won" deals. |

---

## 7. Implementation Roadmap (Hackathon Timeline)

**Phase 1: The Eyes (Data Collection)**
*   Setup N8N workflows.
*   Integrate Perplexity API for news aggregation.
*   Build Python script for scraping pricing pages.

**Phase 2: The Brain (Processing)**
*   Connect Claude API.
*   Design Prompts: "Analyze this HTML diff. Identify if pricing increased. Summarize impact in 2 sentences."
*   Setup Notion Database schema.

**Phase 3: The Voice (Distribution)**
*   Create Notion Battlecard Templates.
*   Build Slack Bot for notifications.
*   (Bonus) Mockup Salesforce widget integration.

**Phase 4: Validation**
*   Run synthetic data test (inject fake competitor news).
*   Measure latency and accuracy of generated summaries.

---

## 8. Challenges & Mitigation

*   **Challenge:** Competitor websites change structure frequently (DOM changes).
    *   *Mitigation:* Use visual regression testing and LLM-based parsing (extracting text rather than relying on CSS selectors) to make scrapers resilient.
*   **Challenge:** Information Overload.
    *   *Mitigation:* Implement an "Impact Score" (1-10). Only events with a score >7 trigger a Slack alert; others go to the weekly digest.