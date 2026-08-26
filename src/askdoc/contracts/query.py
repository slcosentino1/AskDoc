from uuid import UUID

from pydantic import BaseModel, Field


class QueryDocumentsRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class QueryMatch(BaseModel):
    chunk_id: UUID
    job_id: UUID
    file_name: str
    chunk_index: int
    text: str
    score: float


class QueryDocumentsResponse(BaseModel):
    """Full RAG response: retrieved matches plus an LLM-generated answer."""

    query: str
    answer: str
    matches: list[QueryMatch]


class SearchMatchesRequest(BaseModel):
    """Retrieval-only request (no LLM generation)."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class SearchMatchesResponse(BaseModel):
    """Similarity matches for agent/tool clients that generate their own answer."""

    query: str
    matches: list[QueryMatch]
