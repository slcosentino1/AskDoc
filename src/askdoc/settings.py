from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AskDoc"
    environment: str = "local"
    documents_storage_path: Path = Path(".data/documents")
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ASKDOC_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
