# app.py
import re
import streamlit as st
from agents import summarize_youtube_video
from tools import extract_video_id

st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎥",
    layout="wide"
)


def reset_state():
    st.session_state.result = None
    st.session_state.error = None


def is_valid_youtube_url(url: str) -> bool:
    pattern = re.compile(
        r"^(https?://)?(www\.)?"
        r"(youtube\.com/watch\?v=|youtube\.com/shorts/|youtube\.com/embed/|youtu\.be/)"
        r"[\w-]{11}.*$"
    )
    return bool(pattern.match(url.strip()))


def get_friendly_error_message(error: Exception) -> str:
    error_text = str(error).lower()

    if (
        "429" in error_text
        or "resource_exhausted" in error_text
        or "rate limit" in error_text
        or "quota exceeded" in error_text
        or "resource has been exhausted" in error_text
        or "api limit" in error_text
    ):
        return (
            "API usage limit reached for the Gemini service. "
            "Please wait a while and try again later."
        )

    if "invalid youtube url" in error_text:
        return (
            "Invalid YouTube URL. Please enter a valid public YouTube link."
        )

    if "could not extract a valid youtube video id" in error_text:
        return (
            "Could not extract a valid YouTube video ID. "
            "Please use a watch, shorts, embed, or youtu.be link."
        )

    if "transcript unavailable" in error_text:
        return (
            "Transcript is unavailable for this video. "
            "Try another public YouTube video."
        )

    if "transcript not available" in error_text:
        return (
            "Transcript is not available for this video. "
            "Try another public YouTube video."
        )

    if "no transcripts are available" in error_text:
        return (
            "No transcripts are available for this video."
        )

    if "subtitles are disabled" in error_text or "transcripts are disabled" in error_text:
        return (
            "Transcripts are disabled for this video."
        )

    if "video unavailable" in error_text:
        return (
            "This YouTube video is unavailable or inaccessible."
        )

    if "blocked" in error_text and "youtube" in error_text:
        return (
            "Transcript retrieval appears to be blocked by YouTube or the hosting environment. "
            "Please try again later or use another video."
        )

    return (
        "Something went wrong while processing the video. "
        "Please try again later."
    )


if "result" not in st.session_state:
    st.session_state.result = None

if "error" not in st.session_state:
    st.session_state.error = None


st.title("🎥 YouTube Video Summarizer")
st.write("Paste a valid YouTube video URL and generate a clean AI summary with performance metrics.")

video_url = st.text_input(
    "YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=XXXXXXXXXXX"
)

summary_style = st.selectbox(
    "Summary Style",
    ["Detailed", "Short", "Bullet Points", "Study Notes"]
)

col1, col2 = st.columns([3, 1])

with col1:
    summarize_clicked = st.button("Summarize Video", use_container_width=True)

with col2:
    clear_clicked = st.button("Clear", use_container_width=True)

if clear_clicked:
    reset_state()

if summarize_clicked:
    reset_state()

    cleaned_url = video_url.strip()

    if not cleaned_url:
        st.session_state.error = "Please enter a YouTube video URL."

    elif not is_valid_youtube_url(cleaned_url):
        st.session_state.error = (
            "Invalid YouTube URL. Please enter a valid link like:\n"
            "- https://www.youtube.com/watch?v=VIDEO_ID\n"
            "- https://youtu.be/VIDEO_ID\n"
            "- https://www.youtube.com/shorts/VIDEO_ID"
        )

    else:
        video_id = extract_video_id(cleaned_url)

        if not video_id:
            st.session_state.error = (
                "Could not extract a valid YouTube video ID. "
                "Please check the URL and try again."
            )
        else:
            with st.spinner("Fetching transcript and generating summary..."):
                try:
                    result = summarize_youtube_video(cleaned_url, summary_style)
                    st.session_state.result = result

                except Exception as e:
                    st.session_state.error = get_friendly_error_message(e)


if st.session_state.error:
    st.error(st.session_state.error)


if st.session_state.result:
    result = st.session_state.result
    metrics = result.get("metrics", {})

    st.success("Summary generated successfully!")

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Summary")
        st.markdown(result.get("summary", "No summary generated."))

    with right:
        st.subheader("Video Info")
        st.caption(f"Video ID: {result.get('video_id', 'N/A')}")

    st.divider()

    st.subheader("Performance Metrics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Time Taken", f"{metrics.get('time_taken_sec', 0)} sec")
    c2.metric("Transcript Fetch", f"{metrics.get('transcript_fetch_sec', 0)} sec")
    c3.metric("LLM Summary", f"{metrics.get('llm_summary_sec', 0)} sec")

    c4, c5, c6 = st.columns(3)
    c4.metric("Transcript Words", metrics.get("transcript_words", 0))
    c5.metric("Summary Words", metrics.get("summary_words", 0))
    c6.metric("Compression Ratio", metrics.get("compression_ratio", 0))

    c7, c8, c9 = st.columns(3)
    c7.metric("Transcript Chars", metrics.get("transcript_chars", 0))
    c8.metric("Summary Chars", metrics.get("summary_chars", 0))
    c9.metric("Chunks Used", metrics.get("num_chunks", 0))

    with st.expander("Transcript Preview"):
        raw_transcript = result.get("raw_transcript", "")
        st.write(raw_transcript[:5000] + ("..." if len(raw_transcript) > 5000 else ""))

    with st.expander("Detailed Metrics"):
        st.json(metrics)

    st.download_button(
        label="Download Summary",
        data=result.get("summary", ""),
        file_name=f"{result.get('video_id', 'youtube_video')}_summary.txt",
        mime="text/plain",
        use_container_width=True
    )