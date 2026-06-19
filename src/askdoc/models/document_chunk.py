from uuid import UUID

from pydantic import BaseModel


class DocumentChunk(BaseModel):
    chunk_id: UUID
    job_id: UUID
    file_name: str
    chunk_index: int
    text: str
