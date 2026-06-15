"""Offline RAG evaluation harness (RAGAS).

Runs a fixed question set through the real multi-agent pipeline, then scores the
answers with RAGAS metrics — faithfulness, answer relevancy, context precision,
and context recall — using our own Claude model as the judge LLM and the same
all-MiniLM-L6-v2 embeddings the app uses for retrieval.

Run from the project root:
    pip install -r requirements-eval.txt
    python eval/run_eval.py

It ingests the bundled fixtures (eval/fixtures/) into an isolated, throwaway
vector store so it never touches your real document store, prints a metrics
table, writes eval/results.json, and — if Langfuse keys are set — logs the
scores to Langfuse.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Make the project root importable when run as `python eval/run_eval.py`.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.base import AgentStatus  # noqa: E402
from agents.retriever import RetrieverAgent  # noqa: E402
from agents.synthesizer import SynthesizerAgent  # noqa: E402
from agents.web_researcher import WebResearcherAgent  # noqa: E402
from api.dependencies import get_embeddings, get_llm_provider, get_search_provider  # noqa: E402
from config.settings import settings  # noqa: E402
from services.document_processor import DocumentProcessor  # noqa: E402
from services.orchestrator import Orchestrator  # noqa: E402
from services.vector_store import VectorStore  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = EVAL_DIR / "fixtures"
# Isolated store so we never read or clobber the app's real data/qdrant.
EVAL_QDRANT_PATH = str(ROOT / "data" / "qdrant_eval")


async def build_eval_orchestrator() -> tuple[Orchestrator, VectorStore]:
    embeddings = get_embeddings()
    llm = get_llm_provider()
    search = get_search_provider()

    vector_store = VectorStore(dimension=embeddings.dimension, qdrant_path=EVAL_QDRANT_PATH)
    vector_store.clear()  # start from a clean slate each run

    # Ingest fixtures so the Retriever has real grounding contexts.
    processor = DocumentProcessor()
    for path in sorted(FIXTURES_DIR.glob("*")):
        text = path.read_text(encoding="utf-8")
        chunks = processor._chunk_text(text, {"source": path.name, "type": "text"})
        if chunks:
            vectors = embeddings.encode([c.text for c in chunks])
            vector_store.add_documents(chunks, vectors)
    print(f"Ingested fixtures: {vector_store.count} chunks")

    retriever = RetrieverAgent(llm_provider=llm, vector_store=vector_store, embeddings_service=embeddings)
    web_researcher = WebResearcherAgent(llm_provider=llm, search_provider=search)
    synthesizer = SynthesizerAgent(llm_provider=llm)
    return Orchestrator(retriever, web_researcher, synthesizer), vector_store


async def run_pipeline(orchestrator: Orchestrator, question: str) -> tuple[str, list[str]]:
    """Drive the pipeline for one question; return (final_answer, retrieved_contexts)."""
    answer = ""
    contexts: list[str] = []
    async for event in orchestrator.run(question):
        if event.status != AgentStatus.DONE:
            continue
        result = event.data.get("result")
        if result is None:
            continue
        if event.agent_name == "Synthesizer":
            answer = result.content
        else:
            # Retriever / Web Researcher: collect their source snippets as contexts.
            for s in result.sources:
                snippet = s.get("snippet") or s.get("title") or ""
                if snippet:
                    contexts.append(snippet)
    if not contexts:
        contexts = ["(no context retrieved)"]
    return answer, contexts


def score_with_ragas(samples: list[dict]) -> "pd.DataFrame":
    try:
        from ragas import EvaluationDataset, evaluate
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
        from langchain_anthropic import ChatAnthropic
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as e:
        print(
            f"\nERROR: eval dependencies missing ({e}).\n"
            "Install them with:  pip install -r requirements-eval.txt\n"
        )
        sys.exit(1)

    dataset = EvaluationDataset.from_list([
        {
            "user_input": s["question"],
            "response": s["answer"],
            "retrieved_contexts": s["contexts"],
            "reference": s["ground_truth"],
        }
        for s in samples
    ])

    judge_llm = LangchainLLMWrapper(
        ChatAnthropic(model=settings.claude_model, api_key=settings.anthropic_api_key, timeout=60, max_retries=2)
    )
    judge_emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=settings.embedding_model))

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=judge_llm,
        embeddings=judge_emb,
    )
    return result.to_pandas()


async def main():
    dataset = json.loads((EVAL_DIR / "dataset.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(dataset)} eval questions\n")

    orchestrator, _ = await build_eval_orchestrator()

    samples = []
    for i, item in enumerate(dataset, 1):
        q = item["question"]
        print(f"[{i}/{len(dataset)}] {q}")
        answer, contexts = await run_pipeline(orchestrator, q)
        samples.append({
            "question": q,
            "ground_truth": item["ground_truth"],
            "answer": answer,
            "contexts": contexts,
        })

    print("\nScoring with RAGAS (this calls the judge LLM per sample)...\n")
    df = score_with_ragas(samples)

    metric_cols = [c for c in df.columns if c in
                   {"faithfulness", "answer_relevancy", "context_precision", "context_recall"}]
    means = {c: round(float(df[c].mean()), 4) for c in metric_cols}

    print("=" * 48)
    print("RAGAS RESULTS (mean across questions)")
    print("=" * 48)
    for metric, value in means.items():
        print(f"  {metric:.<28} {value}")
    print("=" * 48)

    out = {
        "n_questions": len(dataset),
        "metrics": means,
        "per_sample": df.to_dict(orient="records"),
    }
    (EVAL_DIR / "results.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {EVAL_DIR / 'results.json'}")

    _maybe_log_to_langfuse(means)


def _maybe_log_to_langfuse(means: dict):
    """Log aggregate scores to Langfuse if configured — closes the eval→observability loop."""
    from services.observability import get_langfuse

    client = get_langfuse()
    if client is None:
        return
    try:
        with client.start_as_current_observation(
            as_type="span", name="ragas_eval", input={"dataset": "eval/dataset.json"}, output=means
        ):
            for metric, value in means.items():
                client.score_current_trace(name=metric, value=float(value))
        client.flush()
        print("Logged RAGAS scores to Langfuse.")
    except Exception as e:
        print(f"(Langfuse logging skipped: {e})")


if __name__ == "__main__":
    if not os.path.isdir(FIXTURES_DIR):
        print(f"ERROR: fixtures dir not found at {FIXTURES_DIR}")
        sys.exit(1)
    asyncio.run(main())
