import os
import requests
import asyncio
import edge_tts
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HUGGING_FACE_TOKEN")

def generate_image(prompt: str, output_path: str = "generated_image.jpg"):
    """
    Генерирует картинку через Hugging Face (Flux.1) или Pollinations.
    """
    print(f"🎨 Generating image for: '{prompt}'...")
    try:
        client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=HF_TOKEN)
        image = client.text_to_image(prompt)
        image.save(output_path)
        print(f"✅ Image saved via Flux")
        return output_path
    except Exception as e:
        print(f"⚠️ Flux failed: {e}. Switching to Pollinations...")
        try:
            url = f"https://image.pollinations.ai/prompt/{prompt}"
            response = requests.get(url)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Image saved via Pollinations")
                return output_path
        except Exception as e2:
            print(f"❌ Image generation failed: {e2}")
            return None

async def generate_voice(text: str, output_path: str = "voiceover.mp3"):
    """
    Генерирует голос (Edge TTS).
    """
    print(f"🗣️ Generating voice: '{text[:20]}...'")
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_path)
    print(f"✅ Voice saved to {output_path}")
    return output_path

def generate_sfx(prompt: str, output_path: str = "sfx.mp3"):
    """
    Генерирует звуковые эффекты через Hugging Face (AudioLDM).
    """
    print(f"🔊 Generating SFX for: '{prompt}'...")
    # Update to new router endpoint
    API_URL = "https://router.huggingface.co/models/cvssp/audioldm-m-full"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    payload = {"inputs": prompt}
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✅ SFX saved to {output_path}")
            return output_path
        else:
            print(f"❌ SFX Failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ SFX Error: {e}")
        return None
