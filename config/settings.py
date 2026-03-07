from pydantic_settings import BaseSettings


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

    model_config = {"env_file": ".env"}


settings = Settings()
