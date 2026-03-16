import logging
from typing import AsyncGenerator

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from agents.base import BaseAgent, AgentEvent, AgentResult, AgentStatus
from services.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class WebResearcherAgent(BaseAgent):
    def __init__(self, llm_provider: LLMProvider):
        super().__init__(name="Web Researcher", llm_provider=llm_provider)

    async def execute(self, query: str, context: dict | None = None) -> AsyncGenerator[AgentEvent, None]:
        yield AgentEvent(self.name, AgentStatus.THINKING, "Generating search queries...")

        # Use LLM to generate targeted search queries
        search_queries = await self._generate_search_queries(query)

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

    async def _generate_search_queries(self, query: str) -> list[str]:
        system = "Generate 3 focused search queries to research the user's question. Return ONLY the queries, one per line, no numbering or bullets."

        response = await self.llm_provider.generate(query, system=system)
        queries = [q.strip() for q in response.strip().split("\n") if q.strip()]
        if not queries:
            logger.warning("LLM returned no search queries, falling back to original query")
            return [query]
        return queries[:3]

    async def _search_web(self, queries: list[str]) -> list[dict]:
        results = []
        seen_urls = set()

        for q in queries:
            try:
                with DDGS() as ddgs:
                    for r in ddgs.text(q, max_results=3):
                        if r["href"] not in seen_urls:
                            seen_urls.add(r["href"])
                            results.append({
                                "title": r.get("title", ""),
                                "url": r["href"],
                                "snippet": r.get("body", ""),
                            })
            except (httpx.HTTPError, ConnectionError, TimeoutError) as e:
                logger.warning("Search failed for query %r: %s", q, e)
                continue
            except Exception as e:
                logger.error("Unexpected error during web search for query %r: %s", q, e)
                continue

        # Try to fetch full content for top results
        for r in results[:3]:
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
            f"[{r['title']}]({r['url']})\n{r.get('full_content', r['snippet'])[:1000]}"
            for r in results[:5]
        )

        system = (
            "You are a web research summarizer. Based on the provided web search results, "
            "provide a comprehensive answer to the user's question. Include URLs as citations for claims. "
            "Provide a detailed answer with inline citations [URL]."
        )
        prompt = f"QUESTION: {query}\n\nWEB RESULTS:\n{context}"

        return await self.llm_provider.generate(prompt, system=system)
