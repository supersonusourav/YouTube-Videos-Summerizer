import streamlit as st
from crewai import Agent, Task, Crew, Process, LLM
from langchain_community.tools import DuckDuckGoSearchRun
from tools import get_transcript_or_fallback

def run_yt_crew(topic_or_url):
    # Retrieve keys from Streamlit Secrets (Ops Best Practice)
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_API_KEY"]

    # --- CHEAPEST LLM CONFIGURATION ---
    # Llama 3.3 70B via Groq: Best performance-to-speed ratio for free
    llama_speed = LLM(model="groq/llama-3.3-70b-specdec", api_key=GROQ_KEY)
    
    # DeepSeek V4 Flash: Ultra-low cost (approx ₹11 per 1M tokens) with high reasoning
    deepseek_flash = LLM(model="deepseek/deepseek-v4-flash", api_key=DEEPSEEK_KEY)

    search_tool = DuckDuckGoSearchRun()

    # --- AGENTS ---
    scout = Agent(
        role='Video Scout',
        goal='Find the most relevant YouTube URL for {topic}',
        backstory='Expert in finding authoritative content. You prioritize high-view, educational videos.',
        tools=[search_tool],
        llm=llama_speed
    )

    scribe = Agent(
        role='Transcriber',
        goal='Get the text content for the video URL provided by the Scout.',
        backstory='You extract raw data. You use the provided transcript tools diligently.',
        llm=llama_speed
    )

    architect = Agent(
        role='Knowledge Architect',
        goal='Create a summary, 5 action items, and a Mermaid.js Mind Map code block.',
        backstory='Senior Analyst at Strategic Research Insights. You turn raw text into structured intelligence.',
        llm=deepseek_flash
    )

    # --- TASKS ---
    t1 = Task(description="Find one best YouTube URL for {topic}.", agent=scout, expected_output="A single URL.")
    t2 = Task(description="Extract the transcript for the URL found.", agent=scribe, expected_output="Full video transcript.")
    t3 = Task(description="Synthesize the transcript into a Markdown report with a Mermaid Mind Map.", 
              agent=architect, expected_output="Formatted Markdown with summary and Mermaid code.")

    crew = Crew(agents=[scout, scribe, architect], tasks=[t1, t2, t3], process=Process.sequential)
    return crew.kickoff(inputs={'topic': topic_or_url})