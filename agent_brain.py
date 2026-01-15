import requests
import jwt
import time
import os
import asyncio
import base64
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser

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
    
    # --- METHOD 1: OFFICIAL API ---
    print("\n💎 Trying Official Kling API First...")
    try:
        if not ACCESS_KEY or not SECRET_KEY:
            raise ValueError("Kling API keys missing")
            
        token = generate_jwt_token(ACCESS_KEY, SECRET_KEY)
        
        # 1. Start Task
        url_create = "https://api.klingai.com/v1/videos/image2video"
        
        base64_img = f"data:image/jpeg;base64,{encode_image(image_path)}"
        
        payload = {
            "model_name": "kling-v1", # or kling-v1-6
            "prompt": prompt,
            "image": base64_img, 
            "duration": 10
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url_create, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"⚠️ API Request failed ({response.status_code}): {response.text}")
            raise Exception("API Request returned non-200")
            
        data = response.json()
        task_id = data.get('data', {}).get('task_id')
        if not task_id:
             raise Exception("No task_id in response")
             
        print(f"✅ Task started! ID: {task_id}. Waiting for completion...")
        
        # 2. Poll for result
        for _ in range(30): # Wait up to ~5 minutes
            await asyncio.sleep(10)
            url_status = f"https://api.klingai.com/v1/videos/image2video/{task_id}"
            res_status = requests.get(url_status, headers=headers)
            status_data = res_status.json().get('data', {})
            status = status_data.get('status')
            
            print(f"Status: {status}...")
            if status == 'succeed':
                video_url = status_data.get('video', {}).get('url')
                if not video_url:
                     video_url = status_data.get('output', {}).get('url')
                
                print(f"📥 Downloading video from {video_url}...")
                vid_data = requests.get(video_url).content
                output_filename = f"downloads/kling_{task_id}.mp4"
                os.makedirs("downloads", exist_ok=True)
                with open(output_filename, "wb") as f:
                    f.write(vid_data)
                return output_filename
                
            if status == 'failed':
                 raise Exception(f"Task failed: {status_data}")
        
    except Exception as e:
        print(f"\n❌ API Method Failed: {e}")
        print("🔄 Switching to PLAN B: Browser Agent (The 'Hacker' Way)...")

    # --- METHOD 2: BROWSER AGENT (FALLBACK) ---
    print("\n🤖 Launching Browser Agent...")
    api_key = os.getenv('GOOGLE_API_KEY')
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        api_key=api_key
    )

    task = f"""
    Go to 'https://klingai.com/text-to-video'
    1. If a login button is visible, click it. You (the agent) should try to login using Google if possible.
       Wait 30 seconds for the user to help if automated login fails.
    2. Switch to 'Image to Video' tab.
    3. Upload the image from this absolute path: '{image_path}'.
       - Click the upload area.
       - Use system file picker or input element to select the file.
       - IMPORTANT: Wait for the image to be fully uploaded.
    4. Type the prompt: "{prompt}".
    5. Click the 'Generate' button (it might cost 10 credits).
    6. Wait up to 120 seconds for the generation to complete.
    7. Find the generated video in the list (usually at the top).
    8. Click the 'Download' button for that video.
    """
    
    try:
        # Trying without 'config' argument if it was the issue, or passing simple arguments
        # If Browser(headless=False) fails, we'll try minimal init
        agent = Agent(
            task=task,
            llm=llm,
            # Trying standard Browser initialization, hoping for the best with current version
            browser=Browser() 
        )
        
        await agent.run()
        print("✅ Browser Task Finished. Please check your Downloads folder.")
    except Exception as e:
        print(f"❌ Browser Agent Failed: {e}")
        
    return None
