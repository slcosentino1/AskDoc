from typing import Protocol
from uuid import UUID

from askdoc.contracts.query import QueryMatch


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

    def search(self, *, query_embedding: list[float], top_k: int) -> list[QueryMatch]:
        """Return the top_k chunks most similar to query_embedding (cosine)."""
