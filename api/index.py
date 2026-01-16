from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import os
import shutil
from typing import Optional

# Import our existing modules
from media_gen import generate_image, generate_voice, generate_sfx
from agent_brain import run_kling_agent

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("downloads", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("generated", exist_ok=True)

# Mount static files to serve videos and images
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")
app.mount("/generated", StaticFiles(directory="generated"), name="generated")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

class ImageRequest(BaseModel):
    prompt: str

class VideoRequest(BaseModel):
    prompt: str
    image_path: str
    duration: int = 5

class AudioRequest(BaseModel):
    text: str
    type: str = "voice" # 'voice' or 'sfx'

@app.get("/")
async def root():
    return {"status": "AI Studio Backend Running"}

@app.post("/api/generate-image")
async def api_generate_image(req: ImageRequest):
    try:
        filename = f"generated/img_{int(time.time())}.jpg"
        # Using abstract path for internal usage
        abs_path = os.path.abspath(filename)
        result = generate_image(req.prompt, abs_path)
        if result:
            return {"url": f"/generated/{os.path.basename(filename)}", "path": abs_path}
        else:
            raise HTTPException(status_code=500, detail="Image generation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-video")
async def api_generate_video(req: VideoRequest):
    try:
        # run_kling_agent is async
        video_path = await run_kling_agent(req.prompt, req.image_path)
        
        if not video_path:
            # Check downloads folder fallback logic (similar to main.py)
            downloads_dir = os.path.expanduser("~/Downloads")
            # Wait a bit
            await asyncio.sleep(2)
            list_of_files = [os.path.join(downloads_dir, f) for f in os.listdir(downloads_dir) if f.endswith('.mp4')]
            if list_of_files:
                video_path = max(list_of_files, key=os.path.getctime)
            
        if video_path and os.path.exists(video_path):
            # Move to local downloads static folder for serving
            new_filename = f"kling_video_{int(time.time())}.mp4"
            dest_path = os.path.abspath(os.path.join("downloads", new_filename))
            shutil.copy(video_path, dest_path)
            return {"url": f"/downloads/{new_filename}", "path": dest_path}
        else:
            raise HTTPException(status_code=500, detail="Video generation failed or file not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-audio")
async def api_generate_audio(req: AudioRequest):
    try:
        filename = f"generated/audio_{int(time.time())}.mp3"
        abs_path = os.path.abspath(filename)
        
        if req.type == "voice":
            await generate_voice(req.text, abs_path)
        else:
            generate_sfx(req.text, abs_path)
            
        return {"url": f"/generated/{os.path.basename(filename)}", "path": abs_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_location = f"uploads/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        return {"url": f"/uploads/{file.filename}", "path": os.path.abspath(file_location)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import time
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
