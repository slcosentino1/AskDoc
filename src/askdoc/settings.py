from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AskDoc"
    environment: str = "local"
    documents_storage_path: Path = Path(".data/documents")
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"
    document_chunk_size: int = 500
    document_chunk_overlap: int = 100
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    database_url: str = "postgresql+psycopg://askdoc:askdoc@localhost:5432/askdoc"
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ASKDOC_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
