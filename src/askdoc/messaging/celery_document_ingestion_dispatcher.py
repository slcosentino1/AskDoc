from askdoc.messaging.celery_app import DOCUMENT_INGESTION_TASK, celery_app
from askdoc.models.document_ingestion_job import DocumentIngestionJob


class CeleryDocumentIngestionDispatcher:
    async def dispatch(self, job: DocumentIngestionJob) -> None:
        celery_app.send_task(DOCUMENT_INGESTION_TASK, kwargs=job.model_dump(mode="json"))
