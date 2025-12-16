import requests
import os
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def check_backend():
    print("Checking Backend API Health...")
    host = os.getenv("APP_HOST", "localhost")
    port = os.getenv("APP_PORT", "8000")
    
    urls = [
        f"http://{host}:{port}/health",
        f"http://{host}:{port}/",
        f"http://{host}:{port}/docs"
    ]
    
    success = False
    for url in urls:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f"{GREEN}✅ Backend is UP! (Responding at {url}){RESET}")
                success = True
                break
        except:
            continue
            
    if not success:
        print(f"{RED}❌ Backend Unreachable{RESET}")
        print("   (Ensure 'uvicorn src.main:app' is running)")

if __name__ == "__main__":
    check_backend()
