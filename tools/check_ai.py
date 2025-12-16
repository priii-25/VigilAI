import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def check_ai():
    print("Checking AI Service (Google Gemini)...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
         print(f"{RED}❌ GOOGLE_API_KEY not set{RESET}")
         return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash') # Or 1.5-flash
        
        print("   Sending test prompt: 'Say hello!'...")
        response = await model.generate_content_async("Say hello! Reply with just 'Hello from AI!'")
        
        print(f"{GREEN}✅ AI Working! Response: \"{response.text.strip()}\"{RESET}")
             
    except Exception as e:
        print(f"{RED}❌ AI Failed: {e}{RESET}")

if __name__ == "__main__":
    asyncio.run(check_ai())
