from openai import OpenAI


class OpenAiCompatibleLlmClient:
    """Works with OpenAI, Ollama, LM Studio, and other OpenAI-compatible APIs."""

    def __init__(self, *, api_key: str, model: str, base_url: str | None = None) -> None:
        client_kwargs: dict = {"api_key": api_key or "not-needed"}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = OpenAI(**client_kwargs)
        self._model = model

    def complete(self, *, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
