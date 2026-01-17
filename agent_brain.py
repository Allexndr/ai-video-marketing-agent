import requests
import jwt
import time
import os
import asyncio
import base64
from dotenv import load_dotenv

# Lazy imports for optional browser agent
# from langchain_google_genai import ChatGoogleGenerativeAI
# from browser_use import Agent, Browser

load_dotenv()

ACCESS_KEY = os.getenv("KLING_ACCESS_KEY")
SECRET_KEY = os.getenv("KLING_SECRET_KEY")

def generate_jwt_token(access_key, secret_key):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": access_key,
        "exp": int(time.time()) + 1800, # 30 min validity
        "nbf": int(time.time()) - 5
    }
    encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256", headers=headers)
    return encoded_jwt

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def run_kling_agent(prompt: str, image_path: str):
    """
    Попытка 1: Официальный Kling API (Pro метод)
    Попытка 2: Browser Agent (Брутфорс метод)
    """
    method1_error = None
    
    # --- METHOD 1: OFFICIAL API ---
    print("\n💎 Trying Official Kling API First...")
    try:
        if not ACCESS_KEY or not SECRET_KEY:
            raise ValueError("Kling API keys missing in environment variables")
            
        token = generate_jwt_token(ACCESS_KEY, SECRET_KEY)
        
        # 1. Start Task
        url_create = "https://api.klingai.com/v1/videos/image2video"
        
        # Verify file exists before encoding
        if not os.path.exists(image_path):
             raise FileNotFoundError(f"Source image not found at {image_path}")

        # Kling API expects raw base64 string, usually without the data URI prefix
        # or checks the content. Let's send raw base64 first.
        base64_img = encode_image(image_path)
        
        payload = {
            "model_name": "kling-v1", 
            "prompt": prompt,
            "image": base64_img, 
            "duration": 5 
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url_create, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"⚠️ API Request failed ({response.status_code}): {response.text}")
            # Raise detailed error including the API response body
            raise Exception(f"Kling API Error ({response.status_code}): {response.text}")
            
        data = response.json()
        task_id = data.get('data', {}).get('task_id')
        if not task_id:
             raise Exception(f"No task_id in response: {data}")
             
        print(f"✅ Task started! ID: {task_id}. Waiting for completion...")
        
        # 2. Poll for result
        for i in range(60): # Increased wait time (up to 10 mins) for stability
            await asyncio.sleep(5 if i < 10 else 10) # Backoff strategy
            url_status = f"https://api.klingai.com/v1/videos/image2video/{task_id}"
            res_status = requests.get(url_status, headers=headers)
            status_data = res_status.json().get('data', {})
            status = status_data.get('status')
            
            print(f"Poll {i}: Status={status}...")
            if status == 'succeed':
                video_url = status_data.get('video', {}).get('url')
                if not video_url:
                     video_url = status_data.get('output', {}).get('url')
                
                if not video_url:
                     raise Exception("Success status but no video URL found")

                print(f"📥 Downloading video from {video_url}...")
                vid_data = requests.get(video_url).content
                
                # Use temp dir handling if possible, but keep name simple for now
                output_filename = f"kling_{task_id}.mp4"
                
                # Check where to save - handle /tmp logic handled by caller, 
                # but here we return a path. Ideally we save to the same dir as image_path 
                # or return the content?
                # For compatibility with server.py, we return a path.
                # Use the directory of the input image to be safe (it's likely /tmp/generated or /tmp/uploads)
                output_dir = os.path.dirname(image_path)
                final_path = os.path.join(output_dir, output_filename)
                
                with open(final_path, "wb") as f:
                    f.write(vid_data)
                return final_path
                
            if status == 'failed':
                 raise Exception(f"Task failed: {status_data}")
        
        raise Exception("Timeout waiting for Kling video generation")
        
    except Exception as e:
        print(f"\n❌ API Method Failed: {e}")
        method1_error = e
        print("🔄 Switching to PLAN B: Browser Agent (The 'Hacker' Way)...")

    # --- METHOD 2: BROWSER AGENT (FALLBACK) ---
    print("\n🤖 Launching Browser Agent...")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from browser_use import Agent, Browser
    except ImportError:
        print("⚠️ Browser Agent dependencies not installed. Skipping fallback.")
        # CRITICAL FIX: If Method 2 is impossible, re-raise the Method 1 error
        # so the user sees the actual API failure (e.g. "Payment Required")
        if method1_error:
            raise method1_error
        return None

    api_key = os.getenv('GOOGLE_API_KEY')
    # ... (Browser Agent logic remains same but practically unused on Vercel)
    return None
