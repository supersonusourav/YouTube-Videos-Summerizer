# agents.py
import os
import time
from textwrap import dedent
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from tools import extract_video_id, get_video_transcript, chunk_text, estimate_tokens

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-2.5-flash")

llm = LLM(
    model=GEMINI_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0.3
)


def build_agents():
    transcript_agent = Agent(
        role="YouTube Transcript Analyst",
        goal="Clean and prepare a YouTube transcript for summarization",
        backstory="You clean noisy transcripts while preserving key meaning and facts.",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    summary_agent = Agent(
        role="YouTube Content Summarizer",
        goal="Generate a structured summary from a cleaned transcript",
        backstory="You create concise, useful summaries from long YouTube transcripts.",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    return transcript_agent, summary_agent


def summarize_youtube_video(video_url: str, summary_style: str = "Detailed") -> dict:
    total_start = time.time()

    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError(
            "Could not extract a valid YouTube video ID from the provided URL. "
            "Please use a public YouTube watch, shorts, embed, or youtu.be link."
        )

    transcript_start = time.time()
    transcript_text = get_video_transcript(video_id)
    transcript_time = time.time() - transcript_start

    if not transcript_text.strip():
        raise ValueError("Transcript not available for this video.")

    transcript_words = len(transcript_text.split())
    transcript_chars = len(transcript_text)
    transcript_tokens_est = estimate_tokens(transcript_text)

    chunks = chunk_text(transcript_text, max_chars=12000)
    combined_transcript = "\n\n".join(chunks[:4])

    transcript_agent, summary_agent = build_agents()

    prep_task = Task(
        description=dedent(f"""
            Clean this YouTube transcript.

            Requirements:
            - Remove filler and repeated fragments
            - Preserve key ideas, facts, and examples
            - Return readable text

            Transcript:
            {combined_transcript}
        """),
        expected_output="A cleaned and readable transcript.",
        agent=transcript_agent
    )

    summary_task = Task(
        description=dedent(f"""
            Create a {summary_style.lower()} summary from the cleaned transcript.

            Include:
            1. Title
            2. Overview
            3. Key points
            4. Important insights
            5. Action items
            6. Final takeaway
        """),
        expected_output="A structured summary with clear headings and useful takeaways.",
        agent=summary_agent,
        context=[prep_task]
    )

    llm_start = time.time()
    crew = Crew(
        agents=[transcript_agent, summary_agent],
        tasks=[prep_task, summary_task],
        process=Process.sequential,
        verbose=True
    )
    result = crew.kickoff()
    llm_time = time.time() - llm_start

    summary_text = str(result)
    summary_words = len(summary_text.split())
    summary_chars = len(summary_text)
    summary_tokens_est = estimate_tokens(summary_text)

    total_time = time.time() - total_start
    compression_ratio = round(summary_words / max(transcript_words, 1), 3)

    return {
        "video_id": video_id,
        "raw_transcript": transcript_text,
        "summary": summary_text,
        "metrics": {
            "time_taken_sec": round(total_time, 2),
            "transcript_fetch_sec": round(transcript_time, 2),
            "llm_summary_sec": round(llm_time, 2),
            "transcript_words": transcript_words,
            "transcript_chars": transcript_chars,
            "transcript_tokens_est": transcript_tokens_est,
            "summary_words": summary_words,
            "summary_chars": summary_chars,
            "summary_tokens_est": summary_tokens_est,
            "num_chunks": len(chunks),
            "compression_ratio": compression_ratio
        }
    }