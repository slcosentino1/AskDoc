import logging

from celery.signals import worker_process_init

from askdoc.processing.embeddings import load_embedding_model

logger = logging.getLogger(__name__)


@worker_process_init.connect
def init_worker(**kwargs) -> None:
    """Load heavy resources once per Celery child process (prefork pool)."""
    logger.info("Loading embedding model for worker process...")
    load_embedding_model()
    logger.info("Embedding model loaded")
