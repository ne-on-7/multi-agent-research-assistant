# Multi-Agent Research Assistant

A multi-agent AI system where three specialized agents collaborate to answer research questions from your documents, the web, and GitHub repositories.

## Architecture

```
User Query
    │
    ▼
┌──────────────┐
│  Orchestrator │
└──────┬───────┘
       │
  ┌────┴────┐          (Phase 1: Parallel)
  ▼         ▼
┌─────────┐  ┌──────────────┐
│Retriever│  │Web Researcher│
│ Agent   │  │    Agent     │
└────┬────┘  └──────┬───────┘
     │              │
     └──────┬───────┘
            ▼              (Phase 2: Sequential)
     ┌─────────────┐
     │ Synthesizer │
     │    Agent    │
     └─────────────┘
            │
            ▼
     Final Answer with Citations
```

**Retriever Agent** — Searches your uploaded documents using FAISS vector similarity search, then uses an LLM to extract and summarize relevant passages.

**Web Researcher Agent** — Generates search queries from your question, searches the web via DuckDuckGo, scrapes top results, and summarizes findings.

**Synthesizer Agent** — Combines findings from both agents, resolves conflicts, deduplicates information, and produces a final cited answer streamed in real-time.

## Tech Stack

- **Backend**: FastAPI with SSE streaming
- **Frontend**: Streamlit
- **Vector DB**: FAISS (local)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: Claude (primary) + Gemini (fallback)
- **Web Search**: DuckDuckGo
- **Containerization**: Docker

## Quick Start

### 1. Clone and setup

```bash
cd multi-agent-research-assistant
cp .env.example .env
# Add your API keys to .env
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the backend

```bash
uvicorn api.main:app --reload --port 8000
```

### 4. Run the frontend (in another terminal)

```bash
streamlit run ui/app.py
```

### Or use Docker

```bash
docker-compose up --build
```

## Usage

1. **Upload documents** — Use the sidebar to upload PDFs, paste web URLs, or link GitHub repos
2. **Ask a question** — Type your research question in the main input
3. **Watch agents work** — See real-time activity from all three agents in parallel
4. **Get your answer** — Receive a synthesized answer with numbered citations

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ingest/pdf` | Upload and ingest a PDF |
| POST | `/api/ingest/url` | Ingest content from a URL |
| POST | `/api/ingest/github` | Ingest a GitHub repository |
| GET | `/api/documents` | List ingested documents |
| DELETE | `/api/documents` | Clear all documents |
| POST | `/api/query` | Research query (SSE stream) |
| GET | `/api/health` | Health check |
