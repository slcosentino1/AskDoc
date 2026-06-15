from uuid import uuid4

from askdoc.contracts.documents import IngestDocumentRequest, IngestDocumentResponse
from askdoc.messaging.document_ingestion_dispatcher import DocumentIngestionDispatcher
from askdoc.models.document_ingestion_job import DocumentIngestionJob
from askdoc.storage.document_storage import DocumentStorage


class IngestDocumentUseCase:
    def __init__(self, storage: DocumentStorage, ingestion: DocumentIngestionDispatcher) -> None:
        self._storage = storage
        self._ingestion = ingestion

    async def execute(self, request: IngestDocumentRequest) -> IngestDocumentResponse:
        job_id = uuid4()

        file_path = await self._storage.save(
            job_id=job_id,
            file_name=request.file_name,
            content=request.content,
        )

        await self._ingestion.dispatch(
            job=DocumentIngestionJob(
                job_id=job_id,
                file_name=request.file_name,
                file_path=file_path,
            )
        )

        return IngestDocumentResponse(
            job_id=job_id,
            status="queued",
        )
