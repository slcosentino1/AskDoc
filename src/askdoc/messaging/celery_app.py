from celery import Celery
from kombu import Queue

from askdoc.settings import get_settings

DOCUMENT_INGESTION_QUEUE = "document-ingestion"


def create_celery_app() -> Celery:
    settings = get_settings()

    app = Celery(settings.app_name.lower(), broker=settings.rabbitmq_url)
    app.conf.task_routes = {
        "askdoc.process_document": {
            "queue": DOCUMENT_INGESTION_QUEUE,
            "routing_key": DOCUMENT_INGESTION_QUEUE,
        },
    }

    app.conf.task_queues = (Queue(DOCUMENT_INGESTION_QUEUE),)
    app.conf.task_default_queue = DOCUMENT_INGESTION_QUEUE

    return app


app = create_celery_app()
