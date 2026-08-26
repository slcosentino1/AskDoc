from pytest_mock import MockerFixture

from askdoc.contracts.query import QueryDocumentsRequest, QueryMatch
from askdoc.use_cases.query_documents import QueryDocumentsUseCase


async def test_query_embeds_searches_and_generates(
    mocker: MockerFixture, sample_match: QueryMatch
) -> None:
    fake_embedding = [0.1, 0.2, 0.3]
    mocker.patch(
        "askdoc.use_cases.query_documents.embed_texts",
        return_value=[fake_embedding],
    )

    store = mocker.Mock()
    store.search.return_value = [sample_match]
    llm = mocker.Mock()
    llm.complete.return_value = "Embeddings live in Postgres."
    use_case = QueryDocumentsUseCase(store, llm)

    response = await use_case.execute(
        QueryDocumentsRequest(query="Where are embeddings?", top_k=3)
    )

    assert response.query == "Where are embeddings?"
    assert response.answer == "Embeddings live in Postgres."
    assert response.matches == [sample_match]

    store.search.assert_called_once_with(query_embedding=fake_embedding, top_k=3)
    llm.complete.assert_called_once()
    system = llm.complete.call_args.kwargs["system"]
    user = llm.complete.call_args.kwargs["user"]
    assert "context" in system.lower()
    assert "Where are embeddings?" in user
    assert sample_match.text in user


async def test_query_still_calls_llm_when_no_matches(mocker: MockerFixture) -> None:
    mocker.patch(
        "askdoc.use_cases.query_documents.embed_texts",
        return_value=[[0.0, 0.0, 0.0]],
    )

    store = mocker.Mock()
    store.search.return_value = []
    llm = mocker.Mock()
    llm.complete.return_value = "I don't have enough information."
    use_case = QueryDocumentsUseCase(store, llm)

    response = await use_case.execute(QueryDocumentsRequest(query="Unknown topic?", top_k=5))

    assert response.matches == []
    assert response.answer == "I don't have enough information."
    assert "no matching document chunks" in llm.complete.call_args.kwargs["user"]
