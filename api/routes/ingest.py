import os
import tempfile

from fastapi import APIRouter, File, UploadFile

from api.dependencies import get_document_processor, get_embeddings, get_vector_store
from api.models.schemas import URLRequest, GitHubRequest, IngestResponse, DocumentInfo

router = APIRouter()


@router.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)):
    processor = get_document_processor()
    embeddings = get_embeddings()
    store = get_vector_store()

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        chunks = await processor.process_pdf(tmp_path)
        if chunks:
            vectors = embeddings.encode([c.text for c in chunks])
            store.add_documents(chunks, vectors)
            store.save()
        return IngestResponse(status="success", chunks_added=len(chunks), document_name=file.filename or "upload.pdf")
    finally:
        os.unlink(tmp_path)


@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(request: URLRequest):
    processor = get_document_processor()
    embeddings = get_embeddings()
    store = get_vector_store()

    chunks = await processor.process_url(request.url)
    if chunks:
        vectors = embeddings.encode([c.text for c in chunks])
        store.add_documents(chunks, vectors)
        store.save()

    return IngestResponse(status="success", chunks_added=len(chunks), document_name=request.url)


@router.post("/ingest/github", response_model=IngestResponse)
async def ingest_github(request: GitHubRequest):
    processor = get_document_processor()
    embeddings = get_embeddings()
    store = get_vector_store()

    chunks = await processor.process_github_repo(request.repo_url, request.branch)
    if chunks:
        vectors = embeddings.encode([c.text for c in chunks])
        store.add_documents(chunks, vectors)
        store.save()

    return IngestResponse(status="success", chunks_added=len(chunks), document_name=request.repo_url)


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
    store.clear()
    store.save()
    return {"status": "cleared"}
