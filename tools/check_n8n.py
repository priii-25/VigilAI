import os
import requests
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def check_n8n():
    host = os.getenv("N8N_HOST", "localhost")
    port = os.getenv("N8N_PORT", "5678")
    url = f"http://{host}:{port}"
    print(f"Checking N8N at {url}...")
    
    try:
        r = requests.get(url, timeout=2)
        print(f"{GREEN}✅ N8N is responding! (Status: {r.status_code}){RESET}")
    except Exception as e:
        print(f"{RED}❌ N8N Unreachable: {e}{RESET}")
        print("   (Ensure the N8N container is running: 'docker-compose up -d n8n')")

if __name__ == "__main__":
    check_n8n()
