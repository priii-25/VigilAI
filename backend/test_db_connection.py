
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# Get credentials from env or use defaults from docker-compose
USER = os.getenv("POSTGRES_USER", "vigilai")
PASSWORD = os.getenv("POSTGRES_PASSWORD", "vigilai_password")
DB = os.getenv("POSTGRES_DB", "vigilai")
HOST = "localhost"

async def test_connect(port):
    print(f"\nTesting connection to {HOST}:{port}...")
    dsn = f"postgresql://{USER}:{PASSWORD}@{HOST}:{port}/{DB}"
    try:
        conn = await asyncpg.connect(dsn)
        print(f"SUCCESS! Connected to port {port}")
        await conn.close()
        return True
    except Exception as e:
        print(f"FAILED on port {port}: {str(e)}")
        return False

async def main():
    print(f"User: {USER}")
    print(f"Database: {DB}")
    
    # Test default port 5432 (Local Postgres?)
    success_5432 = await test_connect(5432)
    
    # Test Docker port 5434 (From docker-compose.yml)
    success_5434 = await test_connect(5434)
    
    if success_5434 and not success_5432:
        print("\n💡 SOLUTION: Your database is running on port 5434 (Docker).")
        print("   Please update your backend/.env file:")
        print(f"   DATABASE_URL=postgresql+asyncpg://{USER}:{PASSWORD}@localhost:5434/{DB}")

if __name__ == "__main__":
    asyncio.run(main())
