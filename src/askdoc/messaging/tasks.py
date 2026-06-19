import logging
from uuid import uuid4

from askdoc.messaging.celery_app import DOCUMENT_CHUNKS_TASK, DOCUMENT_INGESTION_TASK, celery_app
from askdoc.models.document_chunk import DocumentChunk
from askdoc.processing.chunking import chunk_document
from askdoc.settings import get_settings

logger = logging.getLogger(__name__)


@celery_app.task(name=DOCUMENT_INGESTION_TASK)
def process_document(job_id: str, file_name: str, file_path: str) -> None:
    """Process the document ingestion job."""
    settings = get_settings()
    chunks_published = 0

    def publish_chunk(chunk_index: int, text: str) -> None:
        nonlocal chunks_published

        chunk = DocumentChunk(
            chunk_id=uuid4(),
            job_id=job_id,
            file_name=file_name,
            chunk_index=chunk_index,
            text=text,
        )

        try:
            celery_app.send_task(DOCUMENT_CHUNKS_TASK, kwargs=chunk.model_dump(mode="json"))
        except Exception:
            logger.exception(
                "Error publishing chunk",
                extra={
                    "job_id": job_id,
                    "chunk_id": chunk.chunk_id,
                    "file_name": file_name,
                    "chunk_index": chunk_index,
                    "text_length": len(text),
                },
            )
            raise

        chunks_published += 1
        logger.info(
            "Publishing chunk",
            extra={
                "job_id": job_id,
                "file_name": file_name,
                "chunk_index": chunk_index,
                "text_length": len(text),
            },
        )

    logger.info(
        "Document ingestion started",
        extra={"job_id": job_id, "file_name": file_name, "file_path": file_path},
    )
    chunk_document(
        file_path,
        settings.document_chunk_size,
        settings.document_chunk_overlap,
        publish_chunk,
    )
    logger.info(
        "Document ingestion finished",
        extra={"job_id": job_id, "chunks_published": chunks_published},
    )


@celery_app.task(name=DOCUMENT_CHUNKS_TASK)
def process_chunk(chunk_id: str, job_id: str, file_name: str, chunk_index: int, text: str) -> None:
    """Process the document chunk job."""
    logger.info(
        "Processing chunk",
        extra={
            "chunk_id": chunk_id,
            "job_id": job_id,
            "chunk_index": chunk_index,
            "file_name": file_name,
            "text_length": len(text),
        },
    )
