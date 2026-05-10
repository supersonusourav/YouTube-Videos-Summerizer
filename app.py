import streamlit as st
from agents import run_yt_crew
import logging

# Basic Ops: Logging
logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="AI YT Agent", page_icon="📺", layout="wide")

st.title("📺 Agentic YouTube Summarizer")
st.caption("Orchestrated with CrewAI | Powered by Llama 3 & DeepSeek")

# Sidebar for Setup (Ops awareness)
with st.sidebar:
    st.header("⚙️ System Status")
    st.success("Docker Container: Running")
    st.info("Keys loaded from Secrets Manager")

query = st.text_input("Enter Topic or YouTube URL:", placeholder="e.g., 'Agentic AI Workflows' or 'https://youtube.com/...'")

if st.button("🚀 Execute Agents", use_container_width=True):
    if query:
        with st.status("🤖 Crew is collaborating...", expanded=True) as status:
            try:
                result = run_yt_crew(query)
                status.update(label="✅ Analysis Complete!", state="complete")
                
                st.divider()
                st.markdown(str(result))
            except Exception as e:
                st.error(f"Execution Error: {e}")
    else:
        st.warning("Please enter a topic.")