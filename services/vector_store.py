from dataclasses import dataclass
from pathlib import Path
import pickle

import faiss
import numpy as np


@dataclass
class DocumentChunk:
    text: str
    metadata: dict


@dataclass
class SearchResult:
    text: str
    metadata: dict
    score: float


class VectorStore:
    def __init__(self, dimension: int = 384, index_path: str = "data/faiss_index"):
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.index = faiss.IndexFlatIP(dimension)
        self.documents: list[DocumentChunk] = []

    def add_documents(self, chunks: list[DocumentChunk], embeddings: np.ndarray):
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        self.documents.extend(chunks)

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> list[SearchResult]:
        query = query_embedding.reshape(1, -1).copy()
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.documents):
                doc = self.documents[idx]
                results.append(SearchResult(text=doc.text, metadata=doc.metadata, score=float(score)))
        return results

    def save(self):
        self.index_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path / "index.faiss"))
        with open(self.index_path / "documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)

    def load(self):
        index_file = self.index_path / "index.faiss"
        if index_file.exists():
            self.index = faiss.read_index(str(index_file))
            with open(self.index_path / "documents.pkl", "rb") as f:
                self.documents = pickle.load(f)

    def clear(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []

    @property
    def count(self) -> int:
        return len(self.documents)
