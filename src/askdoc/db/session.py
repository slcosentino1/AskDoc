from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from askdoc.settings import get_settings

# TODO(async-db): migrate to SQLAlchemy AsyncSession + async driver (e.g. psycopg async
# or asyncpg). Then FastAPI deps and PgVectorStore.search can use await instead of sync
# Session, and QueryDocumentsUseCase won't need to keep search on the request thread.


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_session() -> Session:
    return get_session_factory()()
