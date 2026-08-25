import logging
import re
from collections.abc import Callable, Iterator
from typing import TextIO

logger = logging.getLogger(__name__)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_document(
    file_path: str,
    chunk_size: int,
    overlap: int,
    on_chunk: Callable[[int, str], None],
) -> None:
    """Split a document into chunks on paragraph/sentence boundaries.

    ``chunk_size`` is the max characters per chunk. Small paragraphs are packed
    together until the limit; oversized paragraphs are split on sentences. If a
    single unit still exceeds ``chunk_size``, we break near the last sentence
    punctuation (``.?!``), then ``,``/``;``, then whitespace, and only then fall
    back to a hard cut. If ``overlap`` > 0, each chunk after the first is prefixed
    with the tail of the previous chunk (preferring the last sentence, capped at
    ``overlap`` characters).
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")

    chunk_index = 0
    previous_chunk = ""

    try:
        for piece in _iter_packed_pieces(file_path, chunk_size):
            text = piece
            if chunk_index > 0 and overlap > 0 and previous_chunk:
                prefix = _overlap_prefix(previous_chunk, overlap)
                if prefix:
                    text = f"{prefix} {piece}" if not prefix.endswith("\n") else f"{prefix}{piece}"

            on_chunk(chunk_index, text)
            previous_chunk = text
            chunk_index += 1

    except FileNotFoundError:
        logger.error("File not found: %s", file_path, extra={"file_path": file_path})
        raise

    except PermissionError:
        logger.error(
            "Permission denied reading file: %s",
            file_path,
            extra={"file_path": file_path},
        )
        raise

    except Exception:
        logger.exception(
            "Unexpected error while chunking file: %s",
            file_path,
            extra={"file_path": file_path},
        )
        raise


def _iter_packed_pieces(file_path: str, chunk_size: int) -> Iterator[str]:
    """Yield packed text pieces (no overlap applied yet), streaming by paragraph."""
    buffer = ""

    with open(file_path, encoding="utf-8") as file:
        for paragraph in _iter_paragraphs(file):
            for unit in _paragraph_to_units(paragraph, chunk_size):
                candidate = f"{buffer} {unit}".strip() if buffer else unit
                if buffer and len(candidate) > chunk_size:
                    yield buffer
                    buffer = unit
                else:
                    buffer = candidate

                while len(buffer) > chunk_size:
                    cut = _best_cut(buffer[:chunk_size])
                    piece = buffer[:cut].rstrip()
                    buffer = buffer[cut:].lstrip()
                    if piece:
                        yield piece
                    else:
                        # No progress (leading whitespace window) — force a hard cut.
                        yield buffer[:chunk_size]
                        buffer = buffer[chunk_size:].lstrip()

        if buffer:
            yield buffer


def _iter_paragraphs(file: TextIO) -> Iterator[str]:
    """Yield non-empty paragraphs separated by blank lines."""
    lines: list[str] = []

    for line in file:
        if line.strip() == "":
            paragraph = "".join(lines).strip()
            if paragraph:
                yield paragraph
            lines = []
        else:
            lines.append(line)

    paragraph = "".join(lines).strip()
    if paragraph:
        yield paragraph


def _paragraph_to_units(paragraph: str, chunk_size: int) -> list[str]:
    if len(paragraph) <= chunk_size:
        return [paragraph]

    units: list[str] = []
    for sentence in _SENTENCE_SPLIT.split(paragraph):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= chunk_size:
            units.append(sentence)
        else:
            units.extend(_split_oversized(sentence, chunk_size))
    return units


def _split_oversized(text: str, chunk_size: int) -> list[str]:
    """Split text longer than ``chunk_size`` preferring punctuation, then whitespace."""
    pieces: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= chunk_size:
            pieces.append(remaining)
            break

        cut = _best_cut(remaining[:chunk_size])
        piece = remaining[:cut].rstrip()
        remaining = remaining[cut:].lstrip()

        if piece:
            pieces.append(piece)
        else:
            pieces.append(remaining[:chunk_size])
            remaining = remaining[chunk_size:]

    return pieces


def _best_cut(window: str) -> int:
    """Return a cut index in ``window`` that keeps a natural boundary when possible."""
    for i in range(len(window) - 1, 0, -1):
        if window[i] in ".!?":
            return i + 1

    for i in range(len(window) - 1, 0, -1):
        if window[i] in ",;":
            return i + 1

    for i in range(len(window) - 1, 0, -1):
        if window[i].isspace():
            return i

    return len(window)


def _overlap_prefix(previous_chunk: str, overlap: int) -> str:
    """Prefer the last sentence of the previous chunk, capped at ``overlap`` chars."""
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(previous_chunk) if s.strip()]
    if sentences:
        last = sentences[-1]
        if len(last) <= overlap:
            return last
    return previous_chunk[-overlap:]
