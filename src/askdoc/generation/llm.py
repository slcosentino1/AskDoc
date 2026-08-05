from typing import Protocol


class LlmClient(Protocol):
    def complete(self, *, system: str, user: str) -> str:
        """Generate a completion from system + user messages."""
