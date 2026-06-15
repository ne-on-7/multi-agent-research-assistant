"""Pluggable web search providers.

Tavily is the primary provider when ``TAVILY_API_KEY`` is set — it returns clean,
ranked, LLM-ready content built for AI agents. DuckDuckGo is the zero-config
fallback so the app still works with no keys.

Each provider returns a list of dicts shaped as:
    {"title": str, "url": str, "snippet": str, "full_content": str | None}
When ``full_content`` is present (Tavily), the Web Researcher skips its own
page scrape since the content is already clean.
"""

import asyncio
import logging
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)


class SearchProvider(ABC):
    name: str = "search"

    @abstractmethod
    async def search(self, query: str, max_results: int = 3) -> list[dict]:
        """Return ranked web results for a single query."""
        ...


class TavilyProvider(SearchProvider):
    name = "tavily"

    def __init__(self, api_key: str):
        # Imported lazily so the dependency is only required when actually used.
        from tavily import AsyncTavilyClient

        self.client = AsyncTavilyClient(api_key=api_key)

    async def search(self, query: str, max_results: int = 3) -> list[dict]:
        try:
            response = await self.client.search(
                query, max_results=max_results, search_depth="advanced"
            )
        except Exception as e:
            logger.warning("Tavily search failed for query %r: %s", query, e)
            return []

        results = []
        for r in response.get("results", []):
            content = r.get("content", "") or ""
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": content[:300],
                "full_content": content or None,
            })
        return results


class DDGSProvider(SearchProvider):
    name = "duckduckgo"

    async def search(self, query: str, max_results: int = 3) -> list[dict]:
        # Imported lazily; the network call is sync so run it off the event loop.
        # `ddgs` is the current package (duckduckgo_search was renamed).
        from ddgs import DDGS

        def _run() -> list[dict]:
            out = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    out.append({
                        "title": r.get("title", ""),
                        "url": r["href"],
                        "snippet": r.get("body", ""),
                        "full_content": None,
                    })
            return out

        try:
            return await asyncio.to_thread(_run)
        except (httpx.HTTPError, ConnectionError, TimeoutError) as e:
            logger.warning("DuckDuckGo search failed for query %r: %s", query, e)
            return []
        except Exception as e:
            logger.error("Unexpected error during DuckDuckGo search for query %r: %s", query, e)
            return []


def build_search_provider(tavily_api_key: str = "") -> SearchProvider:
    """Pick Tavily when an API key is available, else fall back to DuckDuckGo."""
    if tavily_api_key:
        logger.info("Web search provider: Tavily")
        return TavilyProvider(api_key=tavily_api_key)
    logger.info("Web search provider: DuckDuckGo (set TAVILY_API_KEY for ranked, LLM-ready results)")
    return DDGSProvider()
