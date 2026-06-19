from fastapi import FastAPI

from askdoc.api.routes import router
from askdoc.logging_config import configure_logging
from askdoc.settings import get_settings

configure_logging()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)
    app.include_router(router, prefix="/api/askdoc")

    return app


app = create_app()
