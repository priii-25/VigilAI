import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try to load from src/core/config if env var not directly available (unlikely in this context but good safety)
    try:
        from src.core.config import settings
        api_key = settings.GOOGLE_API_KEY
    except ImportError:
        print("Could not load API key")
        exit(1)

genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
