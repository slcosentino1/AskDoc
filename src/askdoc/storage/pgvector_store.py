from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from askdoc.contracts.query import QueryMatch
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

    def search(self, *, query_embedding: list[float], top_k: int) -> list[QueryMatch]:
        distance = DocumentChunkEmbedding.embedding.cosine_distance(query_embedding)
        stmt = (
            select(DocumentChunkEmbedding, distance.label("distance"))
            .order_by(distance)
            .limit(top_k)
        )
        rows = self._session.execute(stmt).all()

        matches: list[QueryMatch] = []
        for row in rows:
            chunk = row[0]
            dist = float(row[1])
            matches.append(
                QueryMatch(
                    chunk_id=chunk.chunk_id,
                    job_id=chunk.job_id,
                    file_name=chunk.file_name,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    score=1.0 - dist,
                )
            )
        return matches
