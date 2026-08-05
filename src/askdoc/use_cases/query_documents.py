import asyncio

from askdoc.contracts.query import QueryDocumentsRequest, QueryDocumentsResponse
from askdoc.generation.llm import LlmClient
from askdoc.generation.rag_prompt import build_rag_user_prompt, rag_system_prompt
from askdoc.processing.embeddings import embed_texts
from askdoc.storage.vector_store import VectorStore


class QueryDocumentsUseCase:
    def __init__(self, store: VectorStore, llm: LlmClient) -> None:
        self._store = store
        self._llm = llm

    async def execute(self, request: QueryDocumentsRequest) -> QueryDocumentsResponse:
        embedding = (await asyncio.to_thread(embed_texts, [request.query]))[0]
        # Sync Session is not thread-safe; keep search on the request thread.
        # TODO(async-db): after AsyncSession migration, await store.search(...) instead.
        matches = self._store.search(query_embedding=embedding, top_k=request.top_k)

        answer = await asyncio.to_thread(
            self._llm.complete,
            system=rag_system_prompt(),
            user=build_rag_user_prompt(query=request.query, matches=matches),
        )

        return QueryDocumentsResponse(query=request.query, answer=answer, matches=matches)
