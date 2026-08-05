import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from askdoc.api.routes import router
from askdoc.logging_config import configure_logging
from askdoc.processing.embeddings import load_embedding_model
from askdoc.settings import get_settings

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Loading embedding model for API process...")
    await asyncio.to_thread(load_embedding_model)
    logger.info("Embedding model loaded")
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(router, prefix="/api/askdoc")

    return app


app = create_app()
