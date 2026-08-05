from askdoc.contracts.query import QueryMatch

_SYSTEM_PROMPT = """You are AskDoc, a helpful assistant that answers questions using only the
provided document context.

Rules:
- Base your answer only on the context snippets.
- If the context is empty or insufficient, say you don't have enough information.
- Be concise and cite file names when useful (e.g. according to e2e.txt).
- Do not invent facts that are not in the context.
"""


def build_rag_user_prompt(*, query: str, matches: list[QueryMatch]) -> str:
    if not matches:
        return (
            f"Question: {query}\n\n"
            "Context: (no matching document chunks were found)\n\n"
            "Answer based on the rules."
        )

    parts: list[str] = []
    for i, match in enumerate(matches, start=1):
        parts.append(
            f"[{i}] file={match.file_name} chunk={match.chunk_index} "
            f"score={match.score:.3f}\n{match.text}"
        )
    context = "\n\n".join(parts)
    return f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"


def rag_system_prompt() -> str:
    return _SYSTEM_PROMPT
