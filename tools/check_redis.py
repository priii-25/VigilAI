import asyncio
import os
import sys
import redis.asyncio as redis
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def check_redis():
    print(f"Checking Redis connection...")
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"URL: {url}")
    
    try:
        r = redis.from_url(url)
        await r.ping()
        await r.close()
        print(f"{GREEN}✅ Connected Successfully!{RESET}")
        return True
    except Exception as e:
        print(f"{RED}❌ Connection Failed: {e}{RESET}")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(check_redis())
    except KeyboardInterrupt:
        pass
