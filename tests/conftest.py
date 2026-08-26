"""Shared fixtures. Test packages mirror src/askdoc/ (processing, use_cases, …)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from askdoc.contracts.query import QueryMatch


@pytest.fixture
def sample_match() -> QueryMatch:
    return QueryMatch(
        chunk_id=uuid4(),
        job_id=uuid4(),
        file_name="doc.txt",
        chunk_index=0,
        text="AskDoc stores embeddings in Postgres.",
        score=0.91,
    )
