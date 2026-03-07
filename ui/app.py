import json

import requests
import streamlit as st

from ui.components.sidebar import render_sidebar
from ui.components.agent_panel import render_agent_panels, update_agent_panel
from ui.components.answer_display import render_answer

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")

st.title("Multi-Agent Research Assistant")
st.caption("Upload documents, paste URLs, or link GitHub repos — then ask questions. Three AI agents collaborate to find answers.")

# Sidebar for document ingestion
render_sidebar()

# Query input
query = st.text_input(
    "Ask a research question:",
    placeholder="e.g., What are the key findings in this paper about transformer architectures?",
    key="query_input",
)

if st.button("Research", type="primary", disabled=not query, key="btn_research"):
    # Render agent panels
    panels = render_agent_panels()

    answer_placeholder = st.empty()
    final_answer = ""
    all_sources = []

    try:
        with requests.post(f"{API_URL}/api/query", json={"query": query}, stream=True, timeout=120) as resp:
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue

                line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue

                payload = line[6:]
                if payload == "[DONE]":
                    break

                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    continue

                agent = data.get("agent", "")
                status = data.get("status", "")
                message = data.get("message", "")
                event_data = data.get("data", {})

                # Route event to correct agent panel
                if agent in panels:
                    if event_data.get("type") == "token":
                        # Streaming token from Synthesizer
                        final_answer += message
                        answer_placeholder.markdown(f"**Synthesizing answer...**\n\n{final_answer}")
                    else:
                        update_agent_panel(panels[agent], agent, status, message)

                # Collect sources from final results
                if status == "done" and "result" in event_data:
                    result = event_data["result"]
                    if isinstance(result, dict):
                        all_sources.extend(result.get("sources", []))
                        if agent == "Synthesizer":
                            final_answer = result.get("content", final_answer)

        # Render final answer
        if final_answer:
            # Deduplicate sources
            seen = set()
            unique_sources = []
            for s in all_sources:
                key = s.get("url") or s.get("title", "")
                if key and key not in seen:
                    seen.add(key)
                    unique_sources.append(s)

            render_answer(final_answer, unique_sources)
        else:
            st.warning("No answer was generated. Try uploading documents or rephrasing your question.")

    except requests.ConnectionError:
        st.error("Cannot connect to the API server. Make sure it's running on http://localhost:8000")
    except requests.Timeout:
        st.error("Request timed out. The query may be too complex — try a simpler question.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Footer
st.divider()
st.caption("Built with FastAPI, FAISS, Claude AI & Gemini | Multi-Agent Architecture with Real-Time Streaming")
