import streamlit as st


STATUS_ICONS = {
    "idle": "",
    "thinking": "🧠",
    "searching": "🔍",
    "generating": "✍️",
    "done": "✅",
    "error": "❌",
}


def render_agent_panels():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Retriever Agent")
        st.caption("Searches your uploaded documents")
        if "retriever_events" not in st.session_state:
            st.session_state.retriever_events = []
        retriever_container = st.container()

    with col2:
        st.subheader("Web Researcher")
        st.caption("Searches the web for context")
        if "web_events" not in st.session_state:
            st.session_state.web_events = []
        web_container = st.container()

    with col3:
        st.subheader("Synthesizer")
        st.caption("Combines all findings")
        if "synthesizer_events" not in st.session_state:
            st.session_state.synthesizer_events = []
        synth_container = st.container()

    return {
        "Retriever": retriever_container,
        "Web Researcher": web_container,
        "Synthesizer": synth_container,
    }


def update_agent_panel(container, agent_name: str, status: str, message: str):
    icon = STATUS_ICONS.get(status, "")
    with container:
        st.markdown(f"{icon} **{status.upper()}**: {message}")
