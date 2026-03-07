from typing import AsyncGenerator

from agents.base import BaseAgent, AgentEvent, AgentResult, AgentStatus
from services.llm_provider import LLMProvider


class SynthesizerAgent(BaseAgent):
    def __init__(self, llm_provider: LLMProvider):
        super().__init__(name="Synthesizer", llm_provider=llm_provider)

    async def execute(self, query: str, context: dict | None = None) -> AsyncGenerator[AgentEvent, None]:
        context = context or {}
        retriever_result = context.get("retriever_result")
        web_result = context.get("web_result")

        yield AgentEvent(
            self.name, AgentStatus.THINKING, "Analyzing findings from Retriever and Web Researcher..."
        )

        # Build synthesis prompt
        sections = []

        if retriever_result and retriever_result.content:
            sections.append(f"## Document Analysis (Retriever Agent)\n{retriever_result.content}")

        if web_result and web_result.content:
            sections.append(f"## Web Research Findings\n{web_result.content}")

        if not sections:
            yield AgentEvent(
                self.name,
                AgentStatus.DONE,
                "No findings to synthesize.",
                data={"result": AgentResult(
                    agent_name=self.name,
                    content="Neither the document search nor web research returned useful results. Please try a different query or upload relevant documents.",
                    sources=[],
                    confidence=0.0,
                )},
            )
            return

        combined_findings = "\n\n".join(sections)

        # Collect all sources
        all_sources = []
        if retriever_result:
            all_sources.extend(retriever_result.sources)
        if web_result:
            all_sources.extend(web_result.sources)

        prompt = f"""You are a research synthesizer. Combine the findings from multiple research agents into a single,
comprehensive, well-structured answer. Follow these rules:

1. Merge overlapping information, don't repeat
2. Highlight where document findings and web findings agree or conflict
3. Use numbered citations [1], [2], etc. that map to the sources list
4. Structure the answer with clear sections using markdown
5. End with a "Sources" section listing all references

QUESTION: {query}

RESEARCH FINDINGS:
{combined_findings}

AVAILABLE SOURCES:
{self._format_sources(all_sources)}

Provide the final synthesized answer:"""

        yield AgentEvent(self.name, AgentStatus.GENERATING, "Composing final answer with citations...")

        # Stream the response
        final_answer = ""
        async for token in self.llm_provider.stream(prompt):
            final_answer += token
            yield AgentEvent(self.name, AgentStatus.GENERATING, token, data={"type": "token"})

        confidence = max(
            retriever_result.confidence if retriever_result else 0.0,
            web_result.confidence if web_result else 0.0,
        )

        result = AgentResult(
            agent_name=self.name,
            content=final_answer,
            sources=all_sources,
            confidence=confidence,
        )

        yield AgentEvent(self.name, AgentStatus.DONE, "Synthesis complete.", data={"result": result})

    def _format_sources(self, sources: list[dict]) -> str:
        lines = []
        for i, s in enumerate(sources, 1):
            title = s.get("title", s.get("url", "Unknown"))
            url = s.get("url", "")
            page = s.get("page", "")
            ref = f"[{i}] {title}"
            if url:
                ref += f" - {url}"
            if page:
                ref += f" (Page {page})"
            lines.append(ref)
        return "\n".join(lines)
