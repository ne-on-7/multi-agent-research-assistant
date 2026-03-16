import logging
import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
import httpx

from api.dependencies import get_document_processor, get_embeddings, get_vector_store
from api.models.schemas import URLRequest, GitHubRequest, IngestResponse, DocumentInfo

logger = logging.getLogger(__name__)

MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB

router = APIRouter()


@router.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)):
    processor = get_document_processor()
    embeddings = get_embeddings()
    store = get_vector_store()

    # Check declared size first to reject before reading into memory
    if file.size and file.size > MAX_PDF_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50 MB.")

    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50 MB.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        chunks = await processor.process_pdf(tmp_path)
        if chunks:
            vectors = embeddings.encode([c.text for c in chunks])
            async with store._write_lock:
                store.add_documents(chunks, vectors)
                store.save()
        return IngestResponse(status="success", chunks_added=len(chunks), document_name=file.filename or "upload.pdf")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid PDF: {e}")
    except OSError as e:
        logger.exception("File I/O error processing PDF")
        raise HTTPException(status_code=500, detail="Failed to read PDF file.")
    except Exception:
        logger.exception("Failed to process PDF")
        raise HTTPException(status_code=500, detail="Failed to process PDF.")
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass


@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(request: URLRequest):
    try:
        processor = get_document_processor()
        embeddings = get_embeddings()
        store = get_vector_store()

        chunks = await processor.process_url(str(request.url))
        if chunks:
            vectors = embeddings.encode([c.text for c in chunks])
            async with store._write_lock:
                store.add_documents(chunks, vectors)
                store.save()

        return IngestResponse(status="success", chunks_added=len(chunks), document_name=str(request.url))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL (HTTP {e.response.status_code}).")
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise HTTPException(status_code=502, detail=f"Could not reach URL: {type(e).__name__}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to process URL")
        raise HTTPException(status_code=500, detail="Failed to process URL.")


@router.post("/ingest/github", response_model=IngestResponse)
async def ingest_github(request: GitHubRequest):
    try:
        processor = get_document_processor()
        embeddings = get_embeddings()
        store = get_vector_store()

        chunks = await processor.process_github_repo(request.repo_url, request.branch)
        if chunks:
            vectors = embeddings.encode([c.text for c in chunks])
            async with store._write_lock:
                store.add_documents(chunks, vectors)
                store.save()

        return IngestResponse(status="success", chunks_added=len(chunks), document_name=request.repo_url)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error (HTTP {e.response.status_code}).",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to process GitHub repo")
        raise HTTPException(status_code=500, detail="Failed to process repository.")


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    store = get_vector_store()
    # Group chunks by source
    sources: dict[str, dict] = {}
    for doc in store.documents:
        src = doc.metadata.get("source", "unknown")
        if src not in sources:
            sources[src] = {"name": src, "type": doc.metadata.get("type", "unknown"), "chunks": 0}
        sources[src]["chunks"] += 1
    return [DocumentInfo(**info) for info in sources.values()]


@router.delete("/documents")
async def clear_documents():
    store = get_vector_store()
    async with store._write_lock:
        store.clear()
        store.save()
    return {"status": "cleared"}
