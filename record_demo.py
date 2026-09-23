import asyncio
import os
import glob
import subprocess
import imageio_ffmpeg
from playwright.async_api import async_playwright

FRONTEND_URL = "https://havenscout-frontend-538926441420.us-east1.run.app"
RECORD_DIR = "/config/Desktop/Session1/video_recordings"
OUTPUT_MP4 = "/config/Desktop/Session1/havenscout_demo_video.mp4"
AUDIO_WAV = "/config/Desktop/Session1/lofi_music.wav"

async def record_demo():
    os.makedirs(RECORD_DIR, exist_ok=True)
    
    # Clean up any previous raw recordings
    for f in glob.glob(os.path.join(RECORD_DIR, "*.webm")):
        try: os.remove(f)
        except Exception: pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=RECORD_DIR,
            record_video_size={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        print(f"Navigating to {FRONTEND_URL}...")
        await page.goto(FRONTEND_URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Prompt 1: Apartment Search (Doing what HavenScout does best!)
        prompt_1 = "Find 2 bedroom apartments in Central Austin under $2,500/mo"
        print(f"Typing Prompt 1: '{prompt_1}'...")
        await page.type("#input", prompt_1, delay=40)
        await page.wait_for_timeout(800)
        await page.click("button[type='submit']")

        print("Waiting for HavenScout response to Prompt 1...")
        # Wait until agent message row count is at least 2 (Welcome message + Prompt 1 response)
        await page.wait_for_function("document.querySelectorAll('.msg-row.agent').length >= 2", timeout=30000)
        await page.wait_for_timeout(4000)

        # Smooth scroll to show listings
        await page.evaluate("document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight")
        await page.wait_for_timeout(2000)

        # Prompt 2: Richer prompt showing tool call & image generation!
        prompt_2 = "Generate a realistic interior decor image of a luxury Austin living room with floor to ceiling windows"
        print(f"Typing Prompt 2: '{prompt_2}'...")
        await page.type("#input", prompt_2, delay=35)
        await page.wait_for_timeout(800)
        await page.click("button[type='submit']")

        print("Waiting for HavenScout response to Prompt 2...")
        # Wait until agent message row count is at least 3 (Welcome + Prompt 1 + Prompt 2)
        await page.wait_for_function("document.querySelectorAll('.msg-row.agent').length >= 3", timeout=35000)
        await page.wait_for_timeout(6000)

        # Final scroll down to show generated image & dialogue
        await page.evaluate("document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight")
        await page.wait_for_timeout(4000)

        print("Closing context to save video...")
        await page.close()
        await context.close()
        await browser.close()

def mix_video_and_audio():
    # Find recorded webm file
    webm_files = glob.glob(os.path.join(RECORD_DIR, "*.webm"))
    if not webm_files:
        raise FileNotFoundError("No recorded webm video found in " + RECORD_DIR)
    
    raw_video = max(webm_files, key=os.path.getmtime)
    print(f"Found raw recorded video: {raw_video}")

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    # Merge video and upbeat lo-fi audio, trimming audio to match video duration
    cmd = [
        ffmpeg_exe, "-y",
        "-i", raw_video,
        "-i", AUDIO_WAV,
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_MP4
    ]
    
    print("Combining video with upbeat lo-fi background music via FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg Error Output:", res.stderr)
        raise RuntimeError("FFmpeg video processing failed.")
    
    print(f"SUCCESS: Final demo video created at {OUTPUT_MP4}")

if __name__ == "__main__":
    asyncio.run(record_demo())
    mix_video_and_audio()
