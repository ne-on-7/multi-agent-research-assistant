import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.dependencies import get_orchestrator
from api.models.schemas import QueryRequest
from agents.base import AgentResult

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
        async for event in orchestrator.run(request.query):
            data = {
                "agent": event.agent_name,
                "status": event.status.value,
                "message": event.message,
                "data": event.data,
            }
            yield f"data: {json.dumps(data, default=_serialize)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
