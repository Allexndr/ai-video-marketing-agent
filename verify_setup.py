import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify keys are present
google_key = os.getenv('GOOGLE_API_KEY')
hf_key = os.getenv('HUGGING_FACE_TOKEN')

if not google_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")
else:
    print(f"✅ Google API Key found: {google_key[:10]}...")

if not hf_key:
    print("❌ Error: HUGGING_FACE_TOKEN not found in .env")
else:
    print(f"✅ Hugging Face Token found: {hf_key[:10]}...")

# Install dependencies if you haven't already
# pip install browser-use langchain-google-genai edge-tts requests python-dotenv huggingface_hub
