from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from askdoc.api.routes import (
    get_ingest_document_use_case,
    get_query_documents_use_case,
    get_search_matches_use_case,
    router,
)
from askdoc.contracts.documents import IngestDocumentResponse
from askdoc.contracts.query import QueryDocumentsResponse, QueryMatch, SearchMatchesResponse


def _test_app() -> FastAPI:
    """Thin app with routes only — avoids main.py lifespan (no MiniLM preload)."""
    app = FastAPI()
    app.include_router(router, prefix="/api/askdoc")
    return app


def test_query_route_returns_use_case_response(
    mocker: MockerFixture, sample_match: QueryMatch
) -> None:
    app = _test_app()
    use_case = mocker.AsyncMock()
    use_case.execute.return_value = QueryDocumentsResponse(
        query="What is AskDoc?",
        answer="stub answer",
        matches=[sample_match],
    )
    app.dependency_overrides[get_query_documents_use_case] = lambda: use_case

    with TestClient(app) as client:
        response = client.post(
            "/api/askdoc/query",
            json={"query": "What is AskDoc?", "top_k": 2},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "stub answer"
    assert body["matches"][0]["file_name"] == sample_match.file_name
    use_case.execute.assert_awaited_once()


def test_search_matches_route_returns_matches_without_answer(
    mocker: MockerFixture, sample_match: QueryMatch
) -> None:
    app = _test_app()
    use_case = mocker.AsyncMock()
    use_case.execute.return_value = SearchMatchesResponse(
        query="What is AskDoc?",
        matches=[sample_match],
    )
    app.dependency_overrides[get_search_matches_use_case] = lambda: use_case

    with TestClient(app) as client:
        response = client.post(
            "/api/askdoc/search-matches",
            json={"query": "What is AskDoc?", "top_k": 2},
        )

    assert response.status_code == 200
    body = response.json()
    assert "answer" not in body
    assert body["matches"][0]["file_name"] == sample_match.file_name
    use_case.execute.assert_awaited_once()


def test_query_route_rejects_empty_query() -> None:
    app = _test_app()

    with TestClient(app) as client:
        response = client.post("/api/askdoc/query", json={"query": "", "top_k": 1})

    assert response.status_code == 422


def test_search_matches_route_rejects_empty_query() -> None:
    app = _test_app()

    with TestClient(app) as client:
        response = client.post("/api/askdoc/search-matches", json={"query": "", "top_k": 1})

    assert response.status_code == 422


def test_ingest_route_returns_queued(mocker: MockerFixture) -> None:
    app = _test_app()
    use_case = mocker.AsyncMock()
    use_case.execute.return_value = IngestDocumentResponse(job_id=uuid4(), status="queued")
    app.dependency_overrides[get_ingest_document_use_case] = lambda: use_case

    with TestClient(app) as client:
        response = client.post(
            "/api/askdoc/documents",
            json={"file_name": "a.txt", "content": "hello"},
        )

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    use_case.execute.assert_awaited_once()
