import asyncio
import uuid
from dataclasses import dataclass

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)


@dataclass
class DocumentChunk:
    text: str
    metadata: dict


@dataclass
class SearchResult:
    text: str
    metadata: dict
    score: float


COLLECTION_NAME = "documents"


class VectorStore:
    def __init__(
        self,
        dimension: int = 384,
        qdrant_url: str = "http://localhost:6333",
        qdrant_api_key: str = "",
        qdrant_path: str = "",
    ):
        self.dimension = dimension
        self._write_lock = asyncio.Lock()

        if qdrant_path:
            # Embedded local mode: persists to disk, no server / Docker required.
            self.client = QdrantClient(path=qdrant_path)
        else:
            client_kwargs = {"url": qdrant_url, "timeout": 30}
            if qdrant_api_key:
                client_kwargs["api_key"] = qdrant_api_key
            self.client = QdrantClient(**client_kwargs)

        # Ensure collection exists
        collections = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    def add_documents(self, chunks: list[DocumentChunk], embeddings: np.ndarray):
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={"text": chunk.text, **chunk.metadata},
            )
            for chunk, emb in zip(chunks, embeddings)
        ]
        batch_size = 500
        for i in range(0, len(points), batch_size):
            self.client.upsert(collection_name=COLLECTION_NAME, points=points[i : i + batch_size])

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> list[SearchResult]:
        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding.flatten().tolist(),
            limit=top_k,
        )
        return [
            SearchResult(
                text=hit.payload.get("text", ""),
                metadata={k: v for k, v in hit.payload.items() if k != "text"},
                score=hit.score,
            )
            for hit in results.points
        ]

    def save(self):
        pass  # Qdrant persists automatically

    def load(self):
        pass  # Qdrant persists automatically

    def list_documents(self) -> list[dict]:
        """Return ingested documents grouped by source, scanned from the Qdrant collection."""
        sources: dict[str, dict] = {}
        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=COLLECTION_NAME,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for p in points:
                payload = p.payload or {}
                src = payload.get("source", "unknown")
                if src not in sources:
                    sources[src] = {"name": src, "type": payload.get("type", "unknown"), "chunks": 0}
                sources[src]["chunks"] += 1
            if offset is None:
                break
        return list(sources.values())

    def clear(self):
        self.client.delete_collection(collection_name=COLLECTION_NAME)
        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
        )

    @property
    def count(self) -> int:
        info = self.client.get_collection(COLLECTION_NAME)
        return info.points_count
