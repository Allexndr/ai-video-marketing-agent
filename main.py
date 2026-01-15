import asyncio
import os
import shutil
from media_gen import generate_image, generate_voice, generate_sfx
from agent_brain import run_kling_agent
import subprocess

async def main():
    print("🚗 Starting 'Car Assembly' Video Pipeline...")
    
    # User provided files
    files = [
        "53905470-443a-40cf-abf3-fcc97534a9e2.jpeg",
        "photo_2026-01-14_23-15-02.jpg",
        "cd98c4be-06f8-45c1-aaa0-c956addd038a.jpeg"
    ]
    work_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Select source image
    source_image_name = "photo_2026-01-14_23-15-02.jpg"
    image_path = os.path.join(work_dir, source_image_name)

    if not os.path.exists(image_path):
        print(f"⚠️ Source file {source_image_name} not found in {work_dir}. Trying to find it...")
        # Fallback search strategies
        files = [f for f in os.listdir(work_dir) if f.startswith("photo") and f.endswith(".jpg")]
        if files:
            source_image_name = files[0]
            image_path = os.path.join(work_dir, source_image_name)
            print(f"⚠️ Found similar file: {source_image_name}")
        else:
             print("❌ Could not find the main image. Please check filename.")
             return

    print(f"📸 Using source image: {source_image_name}")

    # 2. Prompts
    video_prompt = (
        "Time-lapse of a white Zeekr car being fully assembled. "
        "Start with an exploded view of parts floating in the air. "
        "Then, watch as the parts RAPIDLY FLY TOGETHER. "
        "The chassis rises, the engine drops in, the body panels and doors SLAM into place. "
        "The car transforms from scattered parts into a SINGLE, SOLID, finished vehicle. "
        "The final frame must show the complete car. "
        "Fast mechanical motion, 4k, studio lighting."
    )
    
    # Mechanical sounds
    sfx_prompt = (
        "Robotic mechanical assembly sounds, pneumatic drills, "
        "metal parts clicking into place, heavy steel clanking, "
        "hydraulic hiss, futuristic garage ambience"
    )

    audio_path = os.path.join(work_dir, "assembly_sfx.mp3")
    
    # 3. Generate Audio (SFX)
    sfx_file = generate_sfx(sfx_prompt, audio_path)
    if not sfx_file:
        print("⚠️ SFX generation failed, proceeding without audio.")
        audio_path = None
    
    # 4. Generate Video (Kling)
    print("\n🎬 Generating Assembly Video via Kling...")
    video_file = await run_kling_agent(video_prompt, image_path)
    
    # Fallback search if agent returns None
    if not video_file:
        downloads_dir = os.path.expanduser("~/Downloads")
        print(f"🔎 Scanning {downloads_dir} for new videos...")
        await asyncio.sleep(5)
        list_of_files = [os.path.join(downloads_dir, f) for f in os.listdir(downloads_dir) if f.endswith('.mp4')]
        if list_of_files:
            video_file = max(list_of_files, key=os.path.getctime)
    
    if not video_file:
        print("❌ Failed to get video file.")
        return

    print(f"✅ Video acquired: {video_file}")
    
    # 5. Merge
    output_file = os.path.join(work_dir, "FINAL_CAR_ASSEMBLY.mp4")
    print("🎞️ Merging video with SFX...")
    
    cmd = ["ffmpeg", "-y", "-i", video_file]
    if audio_path:
        cmd.extend(["-i", audio_path, "-map", "0:v:0", "-map", "1:a:0"])
    else:
        cmd.extend(["-map", "0:v:0"])
        
    cmd.extend(["-c:v", "copy", "-shortest", output_file])
    
    subprocess.run(cmd)
    
    print(f"\n✨ DONE! File: {output_file}")
    subprocess.run(["open", output_file])

if __name__ == "__main__":
    asyncio.run(main())
