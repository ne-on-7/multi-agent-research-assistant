from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.dependencies import get_vector_store

router = APIRouter()


@router.get("/health")
async def health_check():
    try:
        store = get_vector_store()
        store.client.get_collections()
        return {"status": "healthy", "documents": store.count}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})
