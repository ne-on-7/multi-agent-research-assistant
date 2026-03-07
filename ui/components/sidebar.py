import streamlit as st
import requests

API_URL = "http://localhost:8000"


def render_sidebar():
    with st.sidebar:
        st.header("Document Sources")
        st.caption("Upload documents for the agents to research")

        # PDF Upload
        st.subheader("PDF Upload")
        uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"], key="pdf_upload")
        if uploaded_file and st.button("Ingest PDF", key="btn_pdf"):
            with st.spinner("Processing PDF..."):
                resp = requests.post(
                    f"{API_URL}/api/ingest/pdf",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(f"Added {data['chunks_added']} chunks from {data['document_name']}")
                else:
                    st.error(f"Failed: {resp.text}")

        # URL Input
        st.subheader("Web URL")
        url_input = st.text_input("Paste a URL", key="url_input", placeholder="https://example.com/article")
        if url_input and st.button("Ingest URL", key="btn_url"):
            with st.spinner("Fetching URL..."):
                resp = requests.post(f"{API_URL}/api/ingest/url", json={"url": url_input})
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(f"Added {data['chunks_added']} chunks from URL")
                else:
                    st.error(f"Failed: {resp.text}")

        # GitHub Repo
        st.subheader("GitHub Repository")
        github_input = st.text_input("Repo URL", key="github_input", placeholder="https://github.com/owner/repo")
        github_branch = st.text_input("Branch", value="main", key="github_branch")
        if github_input and st.button("Ingest Repo", key="btn_github"):
            with st.spinner("Processing repository..."):
                resp = requests.post(
                    f"{API_URL}/api/ingest/github",
                    json={"repo_url": github_input, "branch": github_branch},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(f"Added {data['chunks_added']} chunks from repo")
                else:
                    st.error(f"Failed: {resp.text}")

        # Document list
        st.divider()
        st.subheader("Ingested Documents")
        try:
            resp = requests.get(f"{API_URL}/api/documents")
            if resp.status_code == 200:
                docs = resp.json()
                if docs:
                    for doc in docs:
                        st.text(f"{doc['type'].upper()}: {doc['name'][:40]}... ({doc['chunks']} chunks)")
                else:
                    st.caption("No documents ingested yet.")
        except requests.ConnectionError:
            st.warning("Backend not running. Start the API server first.")

        if st.button("Clear All Documents", key="btn_clear"):
            requests.delete(f"{API_URL}/api/documents")
            st.rerun()
