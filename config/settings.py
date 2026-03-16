import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    google_api_key: str = ""
    llm_primary: str = "claude"
    llm_fallback: str = "gemini"
    claude_model: str = "claude-sonnet-4-20250514"
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "all-MiniLM-L6-v2"
    faiss_index_path: str = "data/faiss_index"
    chunk_size: int = 512
    chunk_overlap: int = 50
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": ".env"}

    @model_validator(mode="after")
    def validate_api_keys(self):
        missing = []
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        if not self.google_api_key:
            missing.append("GOOGLE_API_KEY")
        if missing:
            raise ValueError(
                f"Missing required API keys: {', '.join(missing)}. "
                "Set them in .env or as environment variables."
            )
        return self


settings = Settings()
