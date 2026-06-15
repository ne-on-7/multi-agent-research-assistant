import asyncio
import logging
from typing import AsyncGenerator

from agents.base import AgentEvent, AgentStatus, BaseAgent
from services.observability import traced_span

logger = logging.getLogger(__name__)

PHASE1_TIMEOUT = 120  # seconds
PHASE2_TIMEOUT = 90  # seconds


class Orchestrator:
    def __init__(self, retriever: BaseAgent, web_researcher: BaseAgent, synthesizer: BaseAgent):
        self.retriever = retriever
        self.web_researcher = web_researcher
        self.synthesizer = synthesizer

    async def run(self, query: str) -> AsyncGenerator[AgentEvent, None]:
        retriever_result = None
        web_result = None

        # Phase 1a: Retriever runs first so its findings can ground the web search.
        try:
            with traced_span("retriever"):
                async with asyncio.timeout(PHASE1_TIMEOUT):
                    async for event in self.retriever.execute(query):
                        if event.status == AgentStatus.DONE and "result" in event.data:
                            retriever_result = event.data["result"]
                        yield event
        except asyncio.TimeoutError:
            logger.error("Retriever timed out after %ds", PHASE1_TIMEOUT)
            yield AgentEvent("Orchestrator", AgentStatus.ERROR, "Document search timed out.")
        except Exception as e:
            logger.exception("Retriever failed")
            yield AgentEvent(self.retriever.name, AgentStatus.ERROR, f"Error: {str(e)}")

        # Phase 1b: Web researcher, grounded with the retriever's findings.
        web_context = {"retriever_result": retriever_result}
        try:
            with traced_span("web_researcher"):
                async with asyncio.timeout(PHASE1_TIMEOUT):
                    async for event in self.web_researcher.execute(query, web_context):
                        if event.status == AgentStatus.DONE and "result" in event.data:
                            web_result = event.data["result"]
                        yield event
        except asyncio.TimeoutError:
            logger.error("Web researcher timed out after %ds", PHASE1_TIMEOUT)
            yield AgentEvent("Orchestrator", AgentStatus.ERROR, "Web research timed out.")
        except Exception as e:
            logger.exception("Web researcher failed")
            yield AgentEvent(self.web_researcher.name, AgentStatus.ERROR, f"Error: {str(e)}")

        # Phase 2: Run Synthesizer with combined results (with timeout)
        context = {"retriever_result": retriever_result, "web_result": web_result}
        try:
            with traced_span("synthesizer"):
                async with asyncio.timeout(PHASE2_TIMEOUT):
                    async for event in self.synthesizer.execute(query, context):
                        yield event
        except asyncio.TimeoutError:
            logger.error("Phase 2 (synthesis) timed out after %ds", PHASE2_TIMEOUT)
            yield AgentEvent("Orchestrator", AgentStatus.ERROR, "Synthesis timed out. Please try again.")
