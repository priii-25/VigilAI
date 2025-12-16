import asyncio
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
load_dotenv(project_root / ".env")

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_result(name, success, message=""):
    icon = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
    print(f"{icon} {name:<25} {message}")

async def check_redis():
    """Check Redis connection"""
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        r = redis.from_url(url)
        await r.ping()
        await r.close()
        return True, "Connected"
    except Exception as e:
        return False, str(e)

async def check_db():
    """Check Database connection"""
    url = os.getenv("DATABASE_URL")
    if not url:
        return False, "DATABASE_URL not set"
    
    # Ensure async driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    
    try:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def check_n8n():
    """Check N8N status"""
    host = os.getenv("N8N_HOST", "localhost")
    port = os.getenv("N8N_PORT", "5678")
    url = f"http://{host}:{port}"
    try:
        requests.get(url, timeout=2) # 404/200/401 are all 'alive'
        return True, f"Running at {url}"
    except Exception as e:
        return False, "Not reachable (is container up?)"

def check_backend():
    """Check Backend Processor"""
    url = f"http://{os.getenv('APP_HOST', 'localhost')}:{os.getenv('APP_PORT', '8000')}/health"
    try:
        # Try root or health
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            return True, "Healthy"
        
        # Try root
        url_root = f"http://{os.getenv('APP_HOST', 'localhost')}:{os.getenv('APP_PORT', '8000')}/"
        r = requests.get(url_root, timeout=2)
        return True, "Responding"
    except:
        return False, "Not reachable"

def check_google_news():
    """Verify Data Collection (Google News)"""
    try:
        # Import service directly to test logic
        from backend.src.services.integrations.google_news_service import GoogleNewsService
        service = GoogleNewsService()
        result = service.search_news("AI functionality test", max_results=1)
        if result.get('success'):
            return True, f"Fetched {len(result.get('articles', []))} articles"
        return False, result.get('error', 'Search failed')
    except ImportError:
        # Try finding via path hack if direct import fails
        sys.path.append(str(project_root / "backend"))
        try:
            from src.services.integrations.google_news_service import GoogleNewsService
            service = GoogleNewsService()
            result = service.search_news("AI functionality test", max_results=1)
            if result.get('success'):
                return True, "Scraping Working"
        except Exception as e:
           return False, f"Import Error: {e}"
    except Exception as e:
        return False, str(e)

async def main():
    print(f"\n🖥️  {GREEN}VigilAI System Health Check{RESET}\n")
    print("-" * 50)
    
    # Infrastructure
    print(f"{YELLOW}Infrastructure:{RESET}")
    
    # Redis
    ok, msg = await check_redis()
    print_result("Redis Cache", ok, msg)
    
    # DB
    ok, msg = await check_db()
    print_result("PostgreSQL Database", ok, msg)
    
    # Services
    print(f"\n{YELLOW}Services:{RESET}")
    
    # Backend
    ok, msg = check_backend()
    print_result("Backend API", ok, msg)
    
    # N8N
    ok, msg = check_n8n()
    print_result("N8N Automation", ok, msg)
    
    # Data Collection
    print(f"\n{YELLOW}Data Collection Engines:{RESET}")
    
    # Google News
    ok, msg = check_google_news()
    print_result("Google News Scraper", ok, msg)
    
    print("-" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
