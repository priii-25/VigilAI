# 🧙‍♂️ VigilAI Setup Wizard

Welcome to the **VigilAI** setup wizard. This guide will help you configure the powerful integrations that make VigilAI a complete competitive intelligence platform.

> **Status Check**: Run `python tools/verify_integrations.py` to see what you are missing!

---

## 🚀 Priority 1: Intelligence Engines (Required)

VigilAI needs these to "think" and find information.

### 1. Google Gemini (Log Analysis)
*Used for: AI-powered root cause analysis of system logs.*

1.  **Get Key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  **Generate**: Create API key.
3.  **Configure**:
    ```env
    GOOGLE_API_KEY=AIzrxxxxxxxxxxxxxxxxxxxx
    ```

> **Note**: News monitoring now uses **Google News RSS (Free)** automatically. No API key required!

---

## 📢 Priority 2: Notifications & Publishing (Highly Recommended)

Connect VigilAI to where your team works.

### 3. Slack Integration (Real-time Alerts)
*Used for: Notifying you when a competitor changes pricing, hires executives, or launches products.*

1.  **Create App**: Go to [Slack API Apps](https://api.slack.com/apps) -> **Create New App** -> **From Scratch**.
2.  **Name It**: "VigilAI Bot".
3.  **Permissions**:
    *   Go to **OAuth & Permissions** (sidebar).
    *   Scroll to **Scopes** -> **Bot Token Scopes**.
    *   Add: `chat:write`, `chat:write.public`, `channels:read`.
4.  **Install**: Scroll up -> **Install to Workspace**.
5.  **Get Token**: Copy the **Bot User OAuth Token** (starts with `xoxb-`).
6.  **Get Channel**:
    *   Create a channel `#competitive-intel`.
    *   Right click channel -> Copy Link -> The ID is the last part (e.g., `C01234567`).
    *   **Important**: Invite the bot to the channel (`/invite @VigilAI Bot`).
7.  **Configure**:
    ```env
    SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
    SLACK_CHANNEL_ID=Cxxxxxxx
    ```

### 4. Notion Integration (Battlecards)
*Used for: Publishing beautiful battlecards for your sales team.*

1.  **Create Integration**: Go to [Notion My Integrations](https://www.notion.so/my-integrations).
2.  **New Integration**: Name it "VigilAI".
3.  **Get Key**: Copy the **Internal Integration Secret**.
4.  **Setup Database**:
    *   [Duplicate this Template](https://www.notion.so/templates) (or create a new database page).
    *   Add properties: `Name` (Title), `Competitor` (Text), `Status` (Select).
    *   **Connect**: Click `...` (top right) -> `Connections` -> Add "VigilAI".
5.  **Get ID**: The Database ID is in the URL between `/` and `?`.
    *   `https://notion.so/myworkspace/DATABASE_ID?v=...`
6.  **Configure**:
    ```env
    NOTION_API_KEY=secret_xxxxxxxxxxxx
    NOTION_DATABASE_ID=xxxxxxxxxxxxxxxx
    ```

---

## 🏁 Verification

Once you have added these to your `.env` file, restart your backend:

```powershell
# Stop current server (Ctrl+C)
uvicorn src.main:app --reload
```

Then run the verification tool again:
```powershell
python tools/verify_integrations.py
```

You should see all ✅ green checks!
