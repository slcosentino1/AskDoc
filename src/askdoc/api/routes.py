from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from askdoc.contracts.documents import IngestDocumentRequest, IngestDocumentResponse
from askdoc.contracts.query import (
    QueryDocumentsRequest,
    QueryDocumentsResponse,
    SearchMatchesRequest,
    SearchMatchesResponse,
)
from askdoc.db.session import get_session
from askdoc.generation.factory import create_llm_client
from askdoc.generation.llm import LlmClient
from askdoc.messaging.celery_document_ingestion_dispatcher import CeleryDocumentIngestionDispatcher
from askdoc.messaging.document_ingestion_dispatcher import DocumentIngestionDispatcher
from askdoc.settings import Settings, get_settings
from askdoc.storage.document_storage import DocumentStorage
from askdoc.storage.local_document_storage import LocalDocumentStorage
from askdoc.storage.pgvector_store import PgVectorStore
from askdoc.storage.vector_store import VectorStore
from askdoc.use_cases.ingest_document import IngestDocumentUseCase
from askdoc.use_cases.query_documents import QueryDocumentsUseCase
from askdoc.use_cases.search_matches import SearchMatchesUseCase

router = APIRouter()


def get_document_storage(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentStorage:
    return LocalDocumentStorage(settings.documents_storage_path)


def get_document_ingestion() -> DocumentIngestionDispatcher:
    return CeleryDocumentIngestionDispatcher()


def get_ingest_document_use_case(
    storage: Annotated[DocumentStorage, Depends(get_document_storage)],
    ingestion: Annotated[DocumentIngestionDispatcher, Depends(get_document_ingestion)],
) -> IngestDocumentUseCase:
    return IngestDocumentUseCase(storage, ingestion)


def get_db_session() -> Iterator[Session]:
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def get_vector_store(
    session: Annotated[Session, Depends(get_db_session)],
) -> VectorStore:
    return PgVectorStore(session)


def get_llm_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LlmClient:
    return create_llm_client(settings)


def get_search_matches_use_case(
    store: Annotated[VectorStore, Depends(get_vector_store)],
) -> SearchMatchesUseCase:
    return SearchMatchesUseCase(store)


def get_query_documents_use_case(
    search: Annotated[SearchMatchesUseCase, Depends(get_search_matches_use_case)],
    llm: Annotated[LlmClient, Depends(get_llm_client)],
) -> QueryDocumentsUseCase:
    return QueryDocumentsUseCase(search, llm)


@router.post(
    "/documents",
    response_model=IngestDocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_document(
    request: IngestDocumentRequest,
    use_case: Annotated[IngestDocumentUseCase, Depends(get_ingest_document_use_case)],
) -> IngestDocumentResponse:
    return await use_case.execute(request)


@router.post(
    "/query",
    response_model=QueryDocumentsResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG query — returns matches and an LLM-generated answer",
)
async def query_documents(
    request: QueryDocumentsRequest,
    use_case: Annotated[QueryDocumentsUseCase, Depends(get_query_documents_use_case)],
) -> QueryDocumentsResponse:
    return await use_case.execute(request)


@router.post(
    "/search-matches",
    response_model=SearchMatchesResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieval only — returns similarity matches (no answer generation)",
)
async def search_matches(
    request: SearchMatchesRequest,
    use_case: Annotated[SearchMatchesUseCase, Depends(get_search_matches_use_case)],
) -> SearchMatchesResponse:
    return await use_case.execute(request)
