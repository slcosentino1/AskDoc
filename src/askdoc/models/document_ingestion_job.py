from pathlib import Path
from uuid import UUID

from pydantic import BaseModel


class DocumentIngestionJob(BaseModel):
    job_id: UUID
    file_name: str
    file_path: Path
