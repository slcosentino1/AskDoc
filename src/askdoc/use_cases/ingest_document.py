from uuid import uuid4

from askdoc.contracts.documents import IngestDocumentRequest, IngestDocumentResponse
from askdoc.storage.document_storage import DocumentStorage


class IngestDocumentUseCase:
    def __init__(self, storage: DocumentStorage) -> None:
        self._storage = storage

    async def execute(self, request: IngestDocumentRequest) -> IngestDocumentResponse:
        job_id = uuid4()
        await self._storage.save(
            job_id=job_id,
            file_name=request.file_name,
            content=request.content,
        )

        return IngestDocumentResponse(
            job_id=job_id,
            status="stored",
        )
