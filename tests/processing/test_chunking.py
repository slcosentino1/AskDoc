from pathlib import Path

import pytest

from askdoc.processing.chunking import chunk_document


def _collect(path: Path, chunk_size: int, overlap: int = 0) -> list[str]:
    chunks: list[str] = []
    chunk_document(
        file_path=str(path),
        chunk_size=chunk_size,
        overlap=overlap,
        on_chunk=lambda _index, text: chunks.append(text),
    )
    return chunks


def test_chunk_document_keeps_short_paragraph_as_one_chunk(tmp_path: Path) -> None:
    path = tmp_path / "short.txt"
    path.write_text("AskDoc stores embeddings in Postgres.", encoding="utf-8")

    assert _collect(path, chunk_size=100) == ["AskDoc stores embeddings in Postgres."]


def test_chunk_document_packs_small_paragraphs_until_size(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("Para one.\n\nPara two.", encoding="utf-8")

    assert _collect(path, chunk_size=40) == ["Para one. Para two."]


def test_chunk_document_splits_when_paragraphs_do_not_fit(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("Para one.\n\nPara two.", encoding="utf-8")

    assert _collect(path, chunk_size=12) == ["Para one.", "Para two."]


def test_chunk_document_splits_long_paragraph_on_sentences(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("Hello world. Goodbye moon.", encoding="utf-8")

    assert _collect(path, chunk_size=15) == ["Hello world.", "Goodbye moon."]


def test_chunk_document_hard_splits_oversized_sentence(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("abcdefghij", encoding="utf-8")

    assert _collect(path, chunk_size=4) == ["abcd", "efgh", "ij"]


def test_chunk_document_breaks_oversized_unit_at_last_period(tmp_path: Path) -> None:
    # No whitespace after "." so sentence-split keeps this as one unit.
    path = tmp_path / "doc.txt"
    path.write_text("aaaa.bbbbcccc", encoding="utf-8")

    assert _collect(path, chunk_size=10) == ["aaaa.", "bbbbcccc"]


def test_chunk_document_breaks_oversized_unit_at_last_comma(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("aaaa,bbbbcccc", encoding="utf-8")

    assert _collect(path, chunk_size=10) == ["aaaa,", "bbbbcccc"]


def test_chunk_document_breaks_oversized_unit_at_last_space(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("hello there friend", encoding="utf-8")

    assert _collect(path, chunk_size=12) == ["hello there", "friend"]


def test_chunk_document_overlap_prefixes_last_sentence(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("Hello world.\n\nGoodbye moon.", encoding="utf-8")

    chunks = _collect(path, chunk_size=15, overlap=20)

    assert chunks[0] == "Hello world."
    assert chunks[1].startswith("Hello world.")
    assert "Goodbye moon." in chunks[1]


def test_chunk_document_raises_when_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        chunk_document(
            file_path=str(missing),
            chunk_size=10,
            overlap=0,
            on_chunk=lambda _i, _t: None,
        )


def test_chunk_document_rejects_non_positive_chunk_size(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("hi", encoding="utf-8")

    with pytest.raises(ValueError, match="chunk_size"):
        chunk_document(
            file_path=str(path),
            chunk_size=0,
            overlap=0,
            on_chunk=lambda _i, _t: None,
        )
