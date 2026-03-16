import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import health, ingest, query
from config.settings import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Research Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(ingest.router, prefix="/api", tags=["ingestion"])
app.include_router(query.router, prefix="/api", tags=["query"])

# Serve built frontend in production
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})
