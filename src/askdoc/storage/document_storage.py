from pathlib import Path
from typing import Protocol
from uuid import UUID


class DocumentStorage(Protocol):
    async def save(self, job_id: UUID, file_name: str, content: str) -> Path:
        """Persist the raw document and return its stored location."""
