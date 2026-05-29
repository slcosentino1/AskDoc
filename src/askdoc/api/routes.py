from typing import Annotated

from fastapi import APIRouter, Depends, status

from askdoc.contracts.documents import IngestDocumentRequest, IngestDocumentResponse
from askdoc.use_cases.ingest_document import IngestDocumentUseCase

router = APIRouter()


def get_ingest_document_use_case() -> IngestDocumentUseCase:
    return IngestDocumentUseCase()


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
