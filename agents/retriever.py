from typing import AsyncGenerator

from agents.base import BaseAgent, AgentEvent, AgentResult, AgentStatus
from services.vector_store import VectorStore
from services.embeddings import EmbeddingsService
from services.llm_provider import LLMProvider


class RetrieverAgent(BaseAgent):
    def __init__(self, llm_provider: LLMProvider, vector_store: VectorStore, embeddings_service: EmbeddingsService):
        super().__init__(name="Retriever", llm_provider=llm_provider)
        self.vector_store = vector_store
        self.embeddings_service = embeddings_service

    async def execute(self, query: str, context: dict | None = None) -> AsyncGenerator[AgentEvent, None]:
        yield AgentEvent(self.name, AgentStatus.SEARCHING, "Searching document store...")

        if self.vector_store.count == 0:
            yield AgentEvent(
                self.name,
                AgentStatus.DONE,
                "No documents ingested yet.",
                data={"result": AgentResult(
                    agent_name=self.name,
                    content="No documents have been uploaded to search.",
                    sources=[],
                    confidence=0.0,
                )},
            )
            return

        query_embedding = self.embeddings_service.encode(query)
        results = self.vector_store.search(query_embedding[0], top_k=10)

        yield AgentEvent(
            self.name, AgentStatus.THINKING, f"Found {len(results)} relevant chunks. Analyzing..."
        )

        # Build extraction prompt
        passages = "\n\n---\n\n".join(
            f"[Source: {r.metadata.get('source', 'unknown')}, Page: {r.metadata.get('page', 'N/A')}]\n{r.text}"
            for r in results[:5]
        )

        system = (
            "Based on the following passages retrieved from uploaded documents, answer the user's question. "
            "Include specific references to which document/page the information came from. "
            "If the passages don't contain enough information, say so clearly. "
            "Provide a detailed, well-structured answer with citations."
        )
        prompt = f"QUESTION: {query}\n\nRETRIEVED PASSAGES:\n{passages}"

        summary = await self.llm_provider.generate(prompt, system=system)

        yield AgentEvent(self.name, AgentStatus.GENERATING, "Compiling document findings...")

        sources = [
            {
                "title": r.metadata.get("source", "unknown"),
                "page": r.metadata.get("page"),
                "snippet": r.text[:200],
                "score": r.score,
            }
            for r in results[:5]
        ]

        confidence = min(1.0, max(r.score for r in results) if results else 0.0)

        result = AgentResult(
            agent_name=self.name,
            content=summary,
            sources=sources,
            confidence=confidence,
        )

        yield AgentEvent(self.name, AgentStatus.DONE, "Document search complete.", data={"result": result})
