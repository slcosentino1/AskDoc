from typing import Protocol

from askdoc.models.document_ingestion_job import DocumentIngestionJob


class DocumentIngestionDispatcher(Protocol):
    async def dispatch(self, job: DocumentIngestionJob) -> None:
        """Send the ingestion job to the async processing backend."""
