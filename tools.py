# tools.py
import re
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str | None:
    try:
        parsed = urlparse(url)

        if parsed.hostname in ["youtu.be"]:
            return parsed.path.lstrip("/")

        if parsed.hostname in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [None])[0]
            if parsed.path.startswith("/shorts/"):
                return parsed.path.split("/shorts/")[1].split("/")[0]
            if parsed.path.startswith("/embed/"):
                return parsed.path.split("/embed/")[1].split("/")[0]

        match = re.search(r"([0-9A-Za-z_-]{11})", url)
        return match.group(1) if match else None
    except Exception:
        return None


def get_video_transcript(video_id: str, preferred_languages=None) -> str:
    preferred_languages = preferred_languages or ["en", "en-US", "hi"]

    api = YouTubeTranscriptApi()

    try:
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(preferred_languages)
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(preferred_languages)
            except Exception:
                available = list(transcript_list)
                if not available:
                    raise ValueError("No transcripts are available for this video.")
                transcript = available[0]

        fetched = transcript.fetch()
        text_parts = [item.text for item in fetched]
        return " ".join(text_parts).strip()

    except Exception as e:
        raise RuntimeError(
            f"Transcript unavailable for video '{video_id}'. "
            f"Possible reasons: no captions, unsupported language, region restriction, or YouTube/IP blocking. "
            f"Original error: {str(e)}"
        )


def chunk_text(text: str, max_chars: int = 12000):
    chunks = []
    current = ""

    for sentence in text.split(". "):
        if len(current) + len(sentence) + 2 <= max_chars:
            current += sentence + ". "
        else:
            chunks.append(current.strip())
            current = sentence + ". "

    if current.strip():
        chunks.append(current.strip())

    return chunks


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.3))