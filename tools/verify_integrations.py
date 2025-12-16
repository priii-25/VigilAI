import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import backend modules if needed
# but for this script we just check env vars
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

def print_status(name, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {name:<20} {details}")

def check_integrations():
    print("\n🔍 VigilAI Integration Status Checker\n")
    print("-" * 50)
    
    # Check AI APIs
    print_status("OpenAI", bool(os.getenv("OPENAI_API_KEY")))
    print_status("Anthropic", bool(os.getenv("ANTHROPIC_API_KEY")))
    # Perplexity removed (using free Google News)
    print_status("Google Gemini", bool(os.getenv("GOOGLE_API_KEY")), "(Used for Log Analysis)")
    
    print("-" * 50)
    
    # Check Integrations
    print_status("Notion API", bool(os.getenv("NOTION_API_KEY")), "(Required for Battlecard Publishing)")
    print_status("Notion DB ID", bool(os.getenv("NOTION_DATABASE_ID")))
    
    print_status("Slack Bot Token", bool(os.getenv("SLACK_BOT_TOKEN")), "(Required for Alerts)")
    print_status("Slack Channel", bool(os.getenv("SLACK_CHANNEL_ID")))
    
    print("-" * 50)
    
    # Check Infrastructure
    print_status("Database URL", bool(os.getenv("DATABASE_URL")))
    print_status("Redis URL", bool(os.getenv("REDIS_URL")))
    
    print("\n💡 To setup missing APIs, refer to SETUP_WIZARD.md")

if __name__ == "__main__":
    check_integrations()
