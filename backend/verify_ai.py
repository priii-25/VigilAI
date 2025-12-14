import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.ai.processor import AIProcessor
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Initializing AI Processor...")
    try:
        processor = AIProcessor()
        print(f"Model: {processor.model.model_name}")
        
        print("Sending test prompt...")
        response = await processor._call_gemini("Hello, say 'AI check successful' if you can hear me.")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
