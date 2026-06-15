import logging
from typing import AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from agents.base import BaseAgent, AgentEvent, AgentResult, AgentStatus
from services.llm_provider import LLMProvider
from services.search_provider import SearchProvider

logger = logging.getLogger(__name__)


class WebResearcherAgent(BaseAgent):
    def __init__(self, llm_provider: LLMProvider, search_provider: SearchProvider):
        super().__init__(name="Web Researcher", llm_provider=llm_provider)
        self.search_provider = search_provider

    async def execute(self, query: str, context: dict | None = None) -> AsyncGenerator[AgentEvent, None]:
        yield AgentEvent(self.name, AgentStatus.THINKING, "Generating search queries...")

        # Use LLM to generate targeted search queries, grounded in the document the
        # retriever found so vague references ("this paper") resolve to the real subject.
        doc_context = self._extract_doc_context(context)
        search_queries = await self._generate_search_queries(query, doc_context)

        yield AgentEvent(
            self.name, AgentStatus.SEARCHING, f"Searching the web with {len(search_queries)} queries..."
        )

        web_results = await self._search_web(search_queries)

        if not web_results:
            yield AgentEvent(
                self.name,
                AgentStatus.DONE,
                "No web results found.",
                data={"result": AgentResult(
                    agent_name=self.name,
                    content="Could not find relevant web results for this query.",
                    sources=[],
                    confidence=0.0,
                )},
            )
            return

        yield AgentEvent(
            self.name, AgentStatus.GENERATING, f"Analyzing {len(web_results)} web results..."
        )

        summary = await self._summarize_findings(query, web_results)

        sources = [
            {"title": r["title"], "url": r["url"], "snippet": r["snippet"][:200]}
            for r in web_results[:5]
        ]

        result = AgentResult(
            agent_name=self.name,
            content=summary,
            sources=sources,
            confidence=0.7,
        )

        yield AgentEvent(self.name, AgentStatus.DONE, "Web research complete.", data={"result": result})

    def _extract_doc_context(self, context: dict | None) -> str:
        """Pull a grounding summary from the retriever's result, if it actually found documents."""
        if not context:
            return ""
        retriever_result = context.get("retriever_result")
        # Only ground when the retriever found real documents (non-empty sources); otherwise
        # leave it empty so general web questions with no uploaded docs still work.
        if retriever_result and getattr(retriever_result, "sources", None) and getattr(retriever_result, "content", ""):
            return retriever_result.content[:1500]
        return ""

    async def _generate_search_queries(self, query: str, doc_context: str = "") -> list[str]:
        system = (
            "You generate web search queries to help answer the user's question. "
            "Output exactly 3 queries, one per line — no numbering, bullets, or quotes. "
            "Each query must be specific and self-contained; never output a single generic word "
            "(e.g. 'paper', 'document', 'study') or anything that would match unrelated topics. "
            "If the question refers to 'this paper', 'the document', 'it', etc., use the DOCUMENT "
            "CONTEXT to identify the real subject (its title or topic) and search for that subject."
        )

        if doc_context:
            user = f"DOCUMENT CONTEXT (what the user's document is about):\n{doc_context}\n\nQUESTION: {query}"
        else:
            user = query

        response = await self.llm_provider.generate(user, system=system)
        queries = [
            q.strip().lstrip("0123456789.-) ").strip()
            for q in response.strip().split("\n")
            if q.strip()
        ]
        queries = [q for q in queries if q]
        if not queries:
            logger.warning("LLM returned no search queries, falling back to original query")
            return [query]
        return queries[:3]

    async def _search_web(self, queries: list[str]) -> list[dict]:
        results = []
        seen_urls = set()

        for q in queries:
            for r in await self.search_provider.search(q, max_results=3):
                url = r.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append(r)

        # Enrich top results with full page content — but only when the provider
        # didn't already return it (Tavily supplies clean content; DuckDuckGo doesn't).
        for r in results[:3]:
            if r.get("full_content"):
                continue
            try:
                content = await self._fetch_page_content(r["url"])
                if content:
                    r["full_content"] = content[:2000]
            except (httpx.HTTPError, ConnectionError, TimeoutError) as e:
                logger.warning("Failed to fetch content from %s: %s", r["url"], e)
            except Exception as e:
                logger.error("Unexpected error fetching %s: %s", r["url"], e)

        return results

    async def _fetch_page_content(self, url: str) -> str | None:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    async def _summarize_findings(self, query: str, results: list[dict]) -> str:
        context = "\n\n---\n\n".join(
            f"[{r['title']}]({r['url']})\n{(r.get('full_content') or r['snippet'])[:1000]}"
            for r in results[:5]
        )

        system = (
            "You are a web research summarizer. Based on the provided web search results, "
            "provide a comprehensive answer to the user's question. Include URLs as citations for claims. "
            "Provide a detailed answer with inline citations [URL]."
        )
        prompt = f"QUESTION: {query}\n\nWEB RESULTS:\n{context}"

        return await self.llm_provider.generate(prompt, system=system)
