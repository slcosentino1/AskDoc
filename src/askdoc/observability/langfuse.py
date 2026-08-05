from functools import lru_cache

from langfuse import Langfuse

from askdoc.settings import Settings


@lru_cache
def configure_langfuse(
    *,
    enabled: bool,
    public_key: str,
    secret_key: str,
    base_url: str,
) -> Langfuse | None:
    if not enabled:
        return None
    if not public_key or not secret_key:
        raise ValueError(
            "Langfuse is enabled but ASKDOC_LANGFUSE_PUBLIC_KEY or "
            "ASKDOC_LANGFUSE_SECRET_KEY is empty."
        )

    return Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        base_url=base_url,
    )


def configure_langfuse_from_settings(settings: Settings) -> Langfuse | None:
    return configure_langfuse(
        enabled=settings.langfuse_enabled,
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        base_url=settings.langfuse_base_url,
    )
