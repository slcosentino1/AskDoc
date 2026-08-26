import asyncio

from langfuse import observe

from askdoc.contracts.query import QueryMatch, SearchMatchesRequest, SearchMatchesResponse
from askdoc.processing.embeddings import embed_texts
from askdoc.storage.vector_store import VectorStore


class SearchMatchesUseCase:
    """Embed a query and return top-k vector matches (no LLM)."""

    def __init__(self, store: VectorStore) -> None:
        self._store = store

    @observe(name="search-matches")
    async def execute(self, request: SearchMatchesRequest) -> SearchMatchesResponse:
        matches = await self._retrieve(query=request.query, top_k=request.top_k)
        return SearchMatchesResponse(query=request.query, matches=matches)

    @observe(name="retrieve-context", as_type="retriever")
    async def _retrieve(self, *, query: str, top_k: int) -> list[QueryMatch]:
        embedding = await self._embed_query(query)
        return self._vector_search(embedding=embedding, top_k=top_k)

    @observe(name="embed-query")
    async def _embed_query(self, query: str) -> list[float]:
        return (await asyncio.to_thread(embed_texts, [query]))[0]

    @observe(name="vector-search")
    def _vector_search(self, *, embedding: list[float], top_k: int) -> list[QueryMatch]:
        # Sync Session is not thread-safe; keep search on the request thread.
        # TODO(async-db): after AsyncSession migration, await store.search(...) instead.
        return self._store.search(query_embedding=embedding, top_k=top_k)
