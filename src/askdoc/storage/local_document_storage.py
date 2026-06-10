import asyncio
from pathlib import Path
from uuid import UUID


class LocalDocumentStorage:
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    async def save(self, job_id: UUID, file_name: str, content: str) -> Path:
        _ = file_name
        target_path = self._base_path / f"{job_id}.txt"

        await asyncio.to_thread(self._write_file, target_path, content)

        return target_path

    @staticmethod
    def _write_file(target_path: Path, content: str) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
