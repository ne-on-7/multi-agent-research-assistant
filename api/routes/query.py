import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.dependencies import get_orchestrator
from api.models.schemas import QueryRequest
from agents.base import AgentResult, AgentStatus
from services.observability import start_trace

router = APIRouter()


def _serialize(obj):
    if isinstance(obj, AgentResult):
        return {
            "agent_name": obj.agent_name,
            "content": obj.content,
            "sources": obj.sources,
            "confidence": obj.confidence,
        }
    return str(obj)


@router.post("/query")
async def research_query(request: QueryRequest):
    orchestrator = get_orchestrator()

    async def event_stream():
        with start_trace("research_query", user_input=request.query) as trace:
            final_answer = ""
            async for event in orchestrator.run(request.query):
                # Capture the synthesizer's final answer for the trace output.
                if event.agent_name == "Synthesizer" and event.status == AgentStatus.DONE:
                    result = event.data.get("result")
                    if result is not None:
                        final_answer = result.content
                data = {
                    "agent": event.agent_name,
                    "status": event.status.value,
                    "message": event.message,
                    "data": event.data,
                }
                yield f"data: {json.dumps(data, default=_serialize)}\n\n"
            trace.update(output=final_answer)
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
