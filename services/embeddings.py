from sentence_transformers import SentenceTransformer
import numpy as np

from config.settings import settings


class EmbeddingsService:
    def __init__(self, model_name: str | None = None):
        self.model = SentenceTransformer(model_name or settings.embedding_model)
        # get_sentence_embedding_dimension was renamed to get_embedding_dimension;
        # prefer the new name, fall back for older sentence-transformers versions.
        get_dim = getattr(self.model, "get_embedding_dimension", None) or self.model.get_sentence_embedding_dimension
        self.dimension = get_dim()

    def encode(self, text: str | list[str]) -> np.ndarray:
        if isinstance(text, str):
            text = [text]
        return self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
