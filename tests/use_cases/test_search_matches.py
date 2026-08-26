from pytest_mock import MockerFixture

from askdoc.contracts.query import QueryMatch, SearchMatchesRequest
from askdoc.use_cases.search_matches import SearchMatchesUseCase


async def test_search_matches_embeds_and_searches(
    mocker: MockerFixture, sample_match: QueryMatch
) -> None:
    fake_embedding = [0.1, 0.2, 0.3]
    mocker.patch(
        "askdoc.use_cases.search_matches.embed_texts",
        return_value=[fake_embedding],
    )

    store = mocker.Mock()
    store.search.return_value = [sample_match]
    use_case = SearchMatchesUseCase(store)

    response = await use_case.execute(SearchMatchesRequest(query="Where are embeddings?", top_k=3))

    assert response.query == "Where are embeddings?"
    assert response.matches == [sample_match]
    assert not hasattr(response, "answer")
    store.search.assert_called_once_with(query_embedding=fake_embedding, top_k=3)


async def test_search_matches_returns_empty_list(mocker: MockerFixture) -> None:
    mocker.patch(
        "askdoc.use_cases.search_matches.embed_texts",
        return_value=[[0.0, 0.0, 0.0]],
    )
    store = mocker.Mock()
    store.search.return_value = []
    use_case = SearchMatchesUseCase(store)

    response = await use_case.execute(SearchMatchesRequest(query="Unknown?", top_k=5))

    assert response.matches == []
