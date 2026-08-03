from typing import Protocol
from uuid import UUID


class VectorStore(Protocol):
    def upsert(
        self,
        *,
        chunk_id: UUID,
        job_id: UUID,
        file_name: str,
        chunk_index: int,
        text: str,
        embedding: list[float],
    ) -> None:
        """Insert or update a chunk embedding by (job_id, chunk_index)."""
