import asyncio

from langfuse import observe

from askdoc.contracts.query import (
    QueryDocumentsRequest,
    QueryDocumentsResponse,
    SearchMatchesRequest,
)
from askdoc.generation.llm import LlmClient
from askdoc.generation.rag_prompt import build_rag_user_prompt, rag_system_prompt
from askdoc.use_cases.search_matches import SearchMatchesUseCase


class QueryDocumentsUseCase:
    """Full RAG: retrieve matches via SearchMatchesUseCase, then generate an answer."""

    def __init__(self, search: SearchMatchesUseCase, llm: LlmClient) -> None:
        self._search = search
        self._llm = llm

    @observe(name="query-documents")
    async def execute(self, request: QueryDocumentsRequest) -> QueryDocumentsResponse:
        retrieved = await self._search.execute(
            SearchMatchesRequest(query=request.query, top_k=request.top_k)
        )
        matches = retrieved.matches

        answer = await asyncio.to_thread(
            self._llm.complete,
            system=rag_system_prompt(),
            user=build_rag_user_prompt(query=request.query, matches=matches),
        )

        return QueryDocumentsResponse(query=request.query, answer=answer, matches=matches)
