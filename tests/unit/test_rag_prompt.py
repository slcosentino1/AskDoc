from askdoc.contracts.query import QueryMatch
from askdoc.generation.rag_prompt import build_rag_user_prompt, rag_system_prompt


def test_rag_system_prompt_mentions_context_only_rule() -> None:
    prompt = rag_system_prompt()
    assert "only the" in prompt.lower() or "only on the context" in prompt.lower()
    assert "do not invent" in prompt.lower()


def test_build_rag_user_prompt_with_matches(sample_match: QueryMatch) -> None:
    prompt = build_rag_user_prompt(query="Where are embeddings stored?", matches=[sample_match])

    assert "Where are embeddings stored?" in prompt
    assert sample_match.file_name in prompt
    assert sample_match.text in prompt
    assert "score=0.910" in prompt


def test_build_rag_user_prompt_without_matches() -> None:
    prompt = build_rag_user_prompt(query="Anything?", matches=[])

    assert "Anything?" in prompt
    assert "no matching document chunks" in prompt
