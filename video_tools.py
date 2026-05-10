# video_tools.py
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
MODEL = os.getenv("GEMINI_VIDEO_MODEL", "gemini-2.5-flash")


def analyze_youtube_video_with_gemini(video_url: str) -> dict:
    start = time.time()

    prompt = """
    Analyze this YouTube video using both audio and visual information.

    Return:
    1. Title or likely topic
    2. Short overview
    3. Key topics discussed
    4. Important visual moments
    5. Scene or slide changes
    6. Actionable takeaways
    7. Timestamped highlights in MM:SS format
    8. A final concise summary

    Be specific about what is visually shown when relevant.
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            {"file_data": {"file_uri": video_url}},
            {"text": prompt}
        ]
    )

    return {
        "analysis": response.text,
        "latency_sec": round(time.time() - start, 2)
    }