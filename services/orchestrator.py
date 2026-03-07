import asyncio
from typing import AsyncGenerator

from agents.base import AgentEvent, AgentStatus, BaseAgent


class Orchestrator:
    def __init__(self, retriever: BaseAgent, web_researcher: BaseAgent, synthesizer: BaseAgent):
        self.retriever = retriever
        self.web_researcher = web_researcher
        self.synthesizer = synthesizer

    async def run(self, query: str) -> AsyncGenerator[AgentEvent, None]:
        retriever_result = None
        web_result = None
        event_queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue()

        async def agent_worker(agent: BaseAgent, result_key: str):
            nonlocal retriever_result, web_result
            try:
                async for event in agent.execute(query):
                    await event_queue.put(event)
                    if event.status == AgentStatus.DONE and "result" in event.data:
                        if result_key == "retriever":
                            retriever_result = event.data["result"]
                        else:
                            web_result = event.data["result"]
            except Exception as e:
                await event_queue.put(
                    AgentEvent(agent.name, AgentStatus.ERROR, f"Error: {str(e)}")
                )
            await event_queue.put(None)  # Signal completion

        # Phase 1: Run Retriever and Web Researcher concurrently
        task1 = asyncio.create_task(agent_worker(self.retriever, "retriever"))
        task2 = asyncio.create_task(agent_worker(self.web_researcher, "web"))

        completed = 0
        while completed < 2:
            event = await event_queue.get()
            if event is None:
                completed += 1
                continue
            yield event

        await asyncio.gather(task1, task2)

        # Phase 2: Run Synthesizer with combined results
        context = {"retriever_result": retriever_result, "web_result": web_result}
        async for event in self.synthesizer.execute(query, context):
            yield event
