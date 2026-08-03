from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from askdoc.db.models import DocumentChunkEmbedding


class PgVectorStore:
    def __init__(self, session: Session) -> None:
        self._session = session

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
        stmt = insert(DocumentChunkEmbedding).values(
            chunk_id=chunk_id,
            job_id=job_id,
            file_name=file_name,
            chunk_index=chunk_index,
            text=text,
            embedding=embedding,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["job_id", "chunk_index"],
            set_={
                "chunk_id": stmt.excluded.chunk_id,
                "file_name": stmt.excluded.file_name,
                "text": stmt.excluded.text,
                "embedding": stmt.excluded.embedding,
            },
        )
        self._session.execute(stmt)
        self._session.commit()
