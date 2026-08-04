import asyncio

from askdoc.contracts.query import QueryDocumentsRequest, QueryDocumentsResponse
from askdoc.processing.embeddings import embed_texts
from askdoc.storage.vector_store import VectorStore


class QueryDocumentsUseCase:
    def __init__(self, store: VectorStore) -> None:
        self._store = store

    async def execute(self, request: QueryDocumentsRequest) -> QueryDocumentsResponse:
        embedding = (await asyncio.to_thread(embed_texts, [request.query]))[0]
        matches = self._store.search(query_embedding=embedding, top_k=request.top_k)
        return QueryDocumentsResponse(query=request.query, matches=matches)
