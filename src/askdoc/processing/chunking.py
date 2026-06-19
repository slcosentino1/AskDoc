import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


def chunk_document(
    file_path: str,
    chunk_size: int,
    overlap: int,
    on_chunk: Callable[[int, str], None],
) -> None:
    chunk_index = 0

    try:
        with open(file_path, encoding="utf-8") as file:
            while True:
                fragment = file.read(chunk_size)

                if not fragment:
                    break

                on_chunk(chunk_index, fragment)

                if len(fragment) < chunk_size:
                    break

                file.seek(file.tell() - overlap)
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
