import logging

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    google_api_key: str = ""
    llm_primary: str = "claude"
    llm_fallback: str = "gemini"
    claude_model: str = "claude-sonnet-4-6"
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "all-MiniLM-L6-v2"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    # When set, Qdrant runs in embedded local mode (persists to this folder, no server/Docker).
    # Leave empty to connect to a Qdrant server at qdrant_url instead.
    qdrant_path: str = "data/qdrant"
    chunk_size: int = 512
    chunk_overlap: int = 50
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    # Web search: Tavily (ranked, LLM-ready) when set, else DuckDuckGo fallback.
    tavily_api_key: str = ""
    # Observability: Langfuse tracing is enabled only when both keys are set.
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    # Canonical name is LANGFUSE_BASE_URL (Langfuse SDK v4); LANGFUSE_HOST still accepted.
    langfuse_base_url: str = Field(
        "https://cloud.langfuse.com",
        validation_alias=AliasChoices("LANGFUSE_BASE_URL", "LANGFUSE_HOST"),
    )

    model_config = {"env_file": ".env", "extra": "ignore"}

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
