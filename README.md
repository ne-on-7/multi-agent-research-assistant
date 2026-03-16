# 🔬 Multi-Agent Research Assistant

A multi-agent AI system where three specialized agents collaborate to answer research questions from your documents, the web, and GitHub repositories — delivering synthesized, cited answers in real time.

---

## 🧠 How It Works

Three AI agents work together, orchestrated in two phases:

```
User Query
    │
    ▼
┌──────────────┐
│  Orchestrator │
└──────┬───────┘
       │
  ┌────┴────┐          ⚡ Phase 1: Parallel
  ▼         ▼
┌─────────┐  ┌──────────────┐
│Retriever│  │Web Researcher│
│ Agent   │  │    Agent     │
└────┬────┘  └──────┬───────┘
     │              │
     └──────┬───────┘
            ▼              🔗 Phase 2: Sequential
     ┌─────────────┐
     │ Synthesizer │
     │    Agent    │
     └─────────────┘
            │
            ▼
     Final Answer with Citations
```

| Agent | What It Does |
|-------|-------------|
| 🔍 **Retriever** | Searches your uploaded documents using FAISS vector similarity, then uses an LLM to extract and summarize relevant passages |
| 🌐 **Web Researcher** | Generates smart search queries from your question, searches the web via DuckDuckGo, scrapes top results, and summarizes findings |
| ✍️ **Synthesizer** | Combines findings from both agents, resolves conflicts, deduplicates info, and produces a final cited answer streamed in real time |

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI + Uvicorn with SSE streaming |
| **Frontend** | React 19 + Vite + Tailwind CSS |
| **LLM** | Claude (primary) + Gemini (fallback) |
| **Vector DB** | FAISS (local) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **Web Search** | DuckDuckGo |
| **Containerization** | Docker + Docker Compose |

---

## 🚀 Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/ne-on-7/multi-agent-research-assistant.git
cd multi-agent-research-assistant
cp .env.example .env
```

Add your API keys to `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
GOOGLE_API_KEY=AIzaxxxxx
```

### 2. Run the app

**Option A — Using the start script (recommended):**

```bash
chmod +x start.sh
./start.sh
```

This installs dependencies, starts the FastAPI backend on `http://localhost:8000`, and the React frontend on `http://localhost:5173`.

**Option B — Using Docker:**

```bash
docker-compose up --build
```

---

## 📖 Usage

1. 📄 **Upload documents** — Use the sidebar to upload PDFs, paste web URLs, or link GitHub repos
2. ❓ **Ask a question** — Type your research question in the main input
3. 👀 **Watch agents work** — See real-time activity from all three agents in parallel
4. ✅ **Get your answer** — Receive a synthesized answer with numbered citations

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ingest/pdf` | Upload and ingest a PDF |
| `POST` | `/api/ingest/url` | Ingest content from a URL |
| `POST` | `/api/ingest/github` | Ingest a GitHub repository |
| `GET` | `/api/documents` | List ingested documents |
| `DELETE` | `/api/documents` | Clear all documents |
| `POST` | `/api/query` | Research query (SSE stream) |
| `GET` | `/api/health` | Health check |

---

## 📁 Project Structure

```
multi-agent-research-assistant/
├── api/                        # FastAPI application
│   ├── main.py                 # App init & middleware
│   ├── routes/                 # API endpoints
│   ├── dependencies.py         # Dependency injection
│   └── models/                 # Pydantic schemas
├── agents/                     # AI agent implementations
│   ├── base.py                 # Base agent class
│   ├── retriever.py            # Document search agent
│   ├── synthesizer.py          # Answer synthesis agent
│   └── web_researcher.py       # Web search agent
├── services/                   # Core business logic
│   ├── orchestrator.py         # Multi-agent coordination
│   ├── llm_provider.py         # LLM abstraction (Claude/Gemini)
│   ├── vector_store.py         # FAISS vector store
│   ├── embeddings.py           # Embedding service
│   └── document_processor.py   # PDF/URL/GitHub processing
├── config/                     # Configuration
│   └── settings.py             # Pydantic settings
├── frontend/                   # React + Vite SPA
│   ├── src/components/         # UI components
│   ├── src/hooks/              # Custom React hooks
│   └── vite.config.js          # Vite config
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── start.sh                    # Dev startup script
└── .env.example                # Environment variable template
```

---

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | — |
| `GOOGLE_API_KEY` | Your Google AI API key | — |
| `LLM_PRIMARY` | Primary LLM provider | `claude` |
| `LLM_FALLBACK` | Fallback LLM provider | `gemini` |
| `CLAUDE_MODEL` | Claude model to use | `claude-sonnet-4-20250514` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.0-flash` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `FAISS_INDEX_PATH` | Path to FAISS index storage | `data/faiss_index` |
