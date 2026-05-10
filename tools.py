import yt_dlp
import logging
from typing import Any, Dict
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger("AgentOps")

def get_transcript_or_fallback(url: str):
    """Tool to fetch transcript with modern 2026 instantiation logic."""
    video_id = url.split("v=")[-1].split("&")[0]
    try:
        logger.info(f"Fetching transcript for {video_id}")
        
        # FIX: Instantiate the API object first (Modern Requirement)
        ytt_api = YouTubeTranscriptApi()
        
        # Use .fetch() which is the stable method for 2026 instances
        transcript = ytt_api.fetch(video_id, languages=['en'])
        
        return " ".join([t.text for t in transcript])
    except Exception as e:
        logger.warning(f"Transcript failed: {e}. Advising agent to request audio extraction.")
        return "ERROR: Transcript unavailable. Please use the Audio Extraction fallback."

def extract_metadata(url: str):
    """Gets video info with explicit typing to resolve linter errors."""
    
    # FIX: Use Any for compatibility with yt_dlp parameter type
    ydl_opts: Any = {
        'quiet': True, 
        'no_warnings': True,
        'skip_download': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Safe access using .get() to prevent Crashes
            title = info.get('title', 'Unknown Title')
            views = info.get('view_count', 'N/A')
            return f"Title: {title}, Views: {views}"
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        return "ERROR: Could not retrieve video metadata."