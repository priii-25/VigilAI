import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
load_dotenv(project_root / ".env")

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def test_slack():
    print("Testing Slack Integration...")
    
    token = os.getenv("SLACK_BOT_TOKEN")
    channel = os.getenv("SLACK_CHANNEL_ID")
    
    if not token or not channel:
        print(f"{RED}❌ Slack credentials missing in .env{RESET}")
        return

    try:
        from slack_sdk import WebClient
        client = WebClient(token=token)
        
        print(f"   Sending test message to channel {channel}...")
        response = client.chat_postMessage(
            channel=channel,
            text="🔔 *VigilAI Test Alert*\nIf you see this, your Slack integration is working perfectly! 🚀"
        )
        
        if response["ok"]:
             print(f"{GREEN}✅ Message Sent Successfully! check your Slack.{RESET}")
        else:
             print(f"{RED}❌ Failed to send: {response['error']}{RESET}")
             
    except ImportError:
        print(f"{RED}❌ Missing dependency: slack_sdk{RESET}")
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")

if __name__ == "__main__":
    asyncio.run(test_slack())
