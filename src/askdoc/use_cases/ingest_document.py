from uuid import uuid4

from askdoc.contracts.documents import IngestDocumentRequest, IngestDocumentResponse


class IngestDocumentUseCase:
    async def execute(self, request: IngestDocumentRequest) -> IngestDocumentResponse:
        job_id = uuid4()

        return IngestDocumentResponse(
            job_id=job_id,
            status="queued",
        )
