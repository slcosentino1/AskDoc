from typing import Annotated

from fastapi import APIRouter, Depends, status

from askdoc.contracts.documents import IngestDocumentRequest, IngestDocumentResponse
from askdoc.messaging.celery_document_ingestion_dispatcher import CeleryDocumentIngestionDispatcher
from askdoc.messaging.document_ingestion_dispatcher import DocumentIngestionDispatcher
from askdoc.settings import Settings, get_settings
from askdoc.storage.document_storage import DocumentStorage
from askdoc.storage.local_document_storage import LocalDocumentStorage
from askdoc.use_cases.ingest_document import IngestDocumentUseCase

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
