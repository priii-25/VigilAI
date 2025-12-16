import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
load_dotenv(project_root / ".env")

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def check_scraper():
    print("Checking Google News Scraper (Data Collection)...")
    
    try:
        # Import service
        from backend.src.services.integrations.google_news_service import GoogleNewsService
        service = GoogleNewsService()
        
        # Try fetch
        query = "Artificial Intelligence"
        print(f"   Fetching news for '{query}'...")
        result = service.search_news(query, max_results=2)
        
        if result.get('success'):
            count = len(result.get('articles', []))
            print(f"{GREEN}✅ Scraper Working! Fetched {count} articles.{RESET}")
            if count > 0:
                print(f"   Sample: {result['articles'][0]['title']}")
        else:
            print(f"{RED}❌ Scraper Failed: {result.get('error')}{RESET}")
            
    except ImportError as e:
        print(f"{RED}❌ Import Error: {e}{RESET}")
        print("   (Ensure you are running from project root or correct environment)")
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")

if __name__ == "__main__":
    check_scraper()
