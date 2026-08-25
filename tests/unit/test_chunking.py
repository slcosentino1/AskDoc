from pathlib import Path

import pytest

from askdoc.processing.chunking import chunk_document


def test_chunk_document_emits_overlapping_chunks(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("abcdefghij", encoding="utf-8")

    chunks: list[tuple[int, str]] = []
    chunk_document(
        file_path=str(path),
        chunk_size=4,
        overlap=2,
        on_chunk=lambda index, text: chunks.append((index, text)),
    )

    assert chunks == [
        (0, "abcd"),
        (1, "cdef"),
        (2, "efgh"),
        (3, "ghij"),
        (4, "ij"),
    ]


def test_chunk_document_single_chunk_when_shorter_than_size(tmp_path: Path) -> None:
    path = tmp_path / "short.txt"
    path.write_text("hi", encoding="utf-8")

    chunks: list[tuple[int, str]] = []
    chunk_document(
        file_path=str(path),
        chunk_size=10,
        overlap=2,
        on_chunk=lambda index, text: chunks.append((index, text)),
    )

    assert chunks == [(0, "hi")]


def test_chunk_document_raises_when_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        chunk_document(
            file_path=str(missing),
            chunk_size=10,
            overlap=2,
            on_chunk=lambda _i, _t: None,
        )
