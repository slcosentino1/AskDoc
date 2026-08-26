from pytest_mock import MockerFixture

from askdoc.contracts.query import QueryDocumentsRequest, QueryMatch, SearchMatchesRequest
from askdoc.use_cases.query_documents import QueryDocumentsUseCase
from askdoc.use_cases.search_matches import SearchMatchesUseCase


async def test_query_retrieves_then_generates(
    mocker: MockerFixture, sample_match: QueryMatch
) -> None:
    search = mocker.AsyncMock(spec=SearchMatchesUseCase)
    search.execute.return_value = mocker.Mock(matches=[sample_match])
    llm = mocker.Mock()
    llm.complete.return_value = "Embeddings live in Postgres."
    use_case = QueryDocumentsUseCase(search, llm)

    response = await use_case.execute(QueryDocumentsRequest(query="Where are embeddings?", top_k=3))

    assert response.query == "Where are embeddings?"
    assert response.answer == "Embeddings live in Postgres."
    assert response.matches == [sample_match]

    search.execute.assert_awaited_once()
    search_req = search.execute.await_args.args[0]
    assert isinstance(search_req, SearchMatchesRequest)
    assert search_req.query == "Where are embeddings?"
    assert search_req.top_k == 3

    llm.complete.assert_called_once()
    system = llm.complete.call_args.kwargs["system"]
    user = llm.complete.call_args.kwargs["user"]
    assert "context" in system.lower()
    assert "Where are embeddings?" in user
    assert sample_match.text in user


async def test_query_still_calls_llm_when_no_matches(mocker: MockerFixture) -> None:
    search = mocker.AsyncMock(spec=SearchMatchesUseCase)
    search.execute.return_value = mocker.Mock(matches=[])
    llm = mocker.Mock()
    llm.complete.return_value = "I don't have enough information."
    use_case = QueryDocumentsUseCase(search, llm)

    response = await use_case.execute(QueryDocumentsRequest(query="Unknown topic?", top_k=5))

    assert response.matches == []
    assert response.answer == "I don't have enough information."
    assert "no matching document chunks" in llm.complete.call_args.kwargs["user"]
