import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def check_db():
    print("Checking Database connection...")
    url = os.getenv("DATABASE_URL")
    
    if not url:
        print(f"{RED}❌ DATABASE_URL not set{RESET}")
        return
        
    print(f"URL: {url.split('@')[-1]}") # Hide credentials
    
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    
    try:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print(f"{GREEN}✅ Connected Successfully!{RESET}")
    except Exception as e:
        print(f"{RED}❌ Connection Failed: {e}{RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(check_db())
    except KeyboardInterrupt:
        pass
