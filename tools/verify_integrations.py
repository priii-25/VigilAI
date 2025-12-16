import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import backend modules if needed
# but for this script we just check env vars
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

def check_val(val):
    """Check if value is present and not a placeholder"""
    if not val:
        return False
    # Check for common placeholder patterns
    if "your_" in val.lower() or "placeholder" in val.lower():
        return False
    return True

def print_status(name, val, details=""):
    is_valid = check_val(val)
    icon = "✅" if is_valid else "❌"
    # Mask actual value if printed (not printing here for security, just bool check passed)
    print(f"{icon} {name:<20} {details}")

def check_integrations():
    print("\n🔍 VigilAI Integration Status Checker\n")
    print("-" * 50)
    
    # Check AI APIs
    print_status("Google Gemini", os.getenv("GOOGLE_API_KEY"), "(Primary AI Engine)")
    
    print("-" * 50)
    
    # Check Integrations
    print_status("Notion API", os.getenv("NOTION_API_KEY"), "(Battlecards)")
    print_status("Notion DB ID", os.getenv("NOTION_DATABASE_ID"))
    
    print_status("Slack Bot Token", os.getenv("SLACK_BOT_TOKEN"), "(Alerts)")
    print_status("Slack Channel", os.getenv("SLACK_CHANNEL_ID"))
    
    print_status("Salesforce Client", os.getenv("SALESFORCE_CLIENT_ID"), "(CRM Integration)")
    print_status("Salesforce User", os.getenv("SALESFORCE_USERNAME"))
    
    print("-" * 50)
    
    # Check Infrastructure
    print_status("Database URL", os.getenv("DATABASE_URL"))
    print_status("Redis URL", os.getenv("REDIS_URL"))
    
    print("\n💡 To setup missing APIs, refer to SETUP_WIZARD.md")

if __name__ == "__main__":
    check_integrations()
