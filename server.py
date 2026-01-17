from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import os
import shutil
import tempfile
import time
from typing import Optional

# Import our existing modules
from media_gen import generate_image, generate_voice, generate_sfx
from agent_brain import run_kling_agent

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel filesystem is read-only except for /tmp
# We will use /tmp for all generated assets
BASE_DIR = tempfile.gettempdir()
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
GENERATED_DIR = os.path.join(BASE_DIR, "generated")

for d in [DOWNLOADS_DIR, UPLOADS_DIR, GENERATED_DIR]:
    os.makedirs(d, exist_ok=True)

class ImageRequest(BaseModel):
    prompt: str

class VideoRequest(BaseModel):
    prompt: str
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    duration: int = 5

@app.post("/api/generate-video")
async def api_generate_video(req: VideoRequest):
    try:
        # Handle Base64 input (Stateless / Vercel compatible)
        if req.image_base64:
            # Create a temp file for the agent to use
            temp_filename = f"temp_source_{int(time.time())}.jpg"
            temp_path = os.path.join(GENERATED_DIR, temp_filename)
            
            # Remove header if present
            b64_data = req.image_base64
            if "," in b64_data:
                b64_data = b64_data.split(",")[1]
                
            with open(temp_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            
            req.image_path = temp_path
            
        # Note: run_kling_agent might fail on Vercel if it tries to use Browser (no browser installed).
        # It relies on specific keys being present for API usage.
        if not req.image_path or not os.path.exists(req.image_path):
             raise HTTPException(status_code=400, detail=f"Source image not found at {req.image_path}")

        video_path = await run_kling_agent(req.prompt, req.image_path)
        
        if not video_path:
            raise HTTPException(status_code=500, detail="Video generation failed (Agent returned None)")
            
        if os.path.exists(video_path):
            new_filename = f"kling_video_{int(time.time())}.mp4"
            dest_path = os.path.join(DOWNLOADS_DIR, new_filename)
            shutil.copy(video_path, dest_path)
            return {"url": f"/api/files/downloads/{new_filename}", "path": dest_path}
        else:
            raise HTTPException(status_code=404, detail="Generated video file not found")
            
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-audio")
async def api_generate_audio(req: AudioRequest):
    try:
        filename = f"audio_{int(time.time())}.mp3"
        abs_path = os.path.join(GENERATED_DIR, filename)
        
        # Ensure directory exists (temp dir might be cleaned up)
        os.makedirs(GENERATED_DIR, exist_ok=True)
        
        if req.type == "voice":
            await generate_voice(req.text, abs_path)
        else:
            # generating sfx
            success = generate_sfx(req.text, abs_path)
            if not success:
                raise HTTPException(status_code=500, detail="HF API failed to generate audio")
            
        return {"url": f"/api/files/generated/{filename}", "path": abs_path}
    except Exception as e:
        print(f"Audio Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        file_location = os.path.join(UPLOADS_DIR, file.filename)
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        return {"url": f"/api/files/uploads/{file.filename}", "path": file_location}
    except Exception as e:
        print(f"Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
