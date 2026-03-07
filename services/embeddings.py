from sentence_transformers import SentenceTransformer
import numpy as np

from config.settings import settings


class EmbeddingsService:
    def __init__(self, model_name: str | None = None):
        self.model = SentenceTransformer(model_name or settings.embedding_model)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def encode(self, text: str | list[str]) -> np.ndarray:
        if isinstance(text, str):
            text = [text]
        return self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
