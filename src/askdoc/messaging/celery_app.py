from celery import Celery
from kombu import Queue

from askdoc.settings import get_settings

DOCUMENT_INGESTION_QUEUE = "document-ingestion"
DOCUMENT_INGESTION_TASK = "askdoc.process_document"


def create_celery_app() -> Celery:
    settings = get_settings()

    celery_app = Celery(settings.app_name.lower(), broker=settings.rabbitmq_url, include=["askdoc.messaging.tasks"])
    celery_app.conf.task_routes = {
        DOCUMENT_INGESTION_TASK: {
            "queue": DOCUMENT_INGESTION_QUEUE,
            "routing_key": DOCUMENT_INGESTION_QUEUE,
        },
    }

    celery_app.conf.task_queues = (Queue(DOCUMENT_INGESTION_QUEUE),)
    celery_app.conf.task_default_queue = DOCUMENT_INGESTION_QUEUE

    return celery_app


celery_app = create_celery_app()
