from uuid import UUID

from pydantic import BaseModel, Field


class IngestDocumentRequest(BaseModel):
    file_name: str = Field(min_length=1)
    content: str = Field(min_length=1)


class IngestDocumentResponse(BaseModel):
    job_id: UUID
    status: str
