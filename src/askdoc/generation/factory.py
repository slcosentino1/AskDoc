from askdoc.generation.llm import LlmClient
from askdoc.generation.openai_compatible import OpenAiCompatibleLlmClient
from askdoc.observability.langfuse import configure_langfuse_from_settings
from askdoc.settings import Settings

_OPENAI_COMPATIBLE_PROVIDERS = frozenset({"ollama", "openai", "openai_compatible"})


def create_llm_client(settings: Settings) -> LlmClient:
    configure_langfuse_from_settings(settings)

    provider = settings.llm_provider.strip().lower()
    if provider not in _OPENAI_COMPATIBLE_PROVIDERS:
        raise ValueError(
            f"Unsupported ASKDOC_LLM_PROVIDER={settings.llm_provider!r}. "
            f"Supported: {', '.join(sorted(_OPENAI_COMPATIBLE_PROVIDERS))}"
        )

    base_url = settings.llm_base_url.strip() or None
    if provider == "ollama" and base_url is None:
        base_url = "http://localhost:11434/v1"

    return OpenAiCompatibleLlmClient(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=base_url,
        trace_enabled=settings.langfuse_enabled,
    )
