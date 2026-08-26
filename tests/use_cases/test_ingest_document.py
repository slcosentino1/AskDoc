from pathlib import Path

from pytest_mock import MockerFixture

from askdoc.contracts.documents import IngestDocumentRequest
from askdoc.use_cases.ingest_document import IngestDocumentUseCase


async def test_ingest_saves_document_and_dispatches_job(mocker: MockerFixture) -> None:
    storage = mocker.AsyncMock()

    async def save(*, job_id, file_name, content):
        return Path(f"/tmp/{job_id}.txt")

    storage.save.side_effect = save
    dispatcher = mocker.AsyncMock()
    use_case = IngestDocumentUseCase(storage, dispatcher)

    response = await use_case.execute(
        IngestDocumentRequest(file_name="notes.txt", content="hello ingest")
    )

    assert response.status == "queued"
    storage.save.assert_awaited_once()
    save_kwargs = storage.save.await_args.kwargs
    assert save_kwargs["job_id"] == response.job_id
    assert save_kwargs["file_name"] == "notes.txt"
    assert save_kwargs["content"] == "hello ingest"

    dispatcher.dispatch.assert_awaited_once()
    job = dispatcher.dispatch.await_args.kwargs["job"]
    assert job.job_id == response.job_id
    assert job.file_name == "notes.txt"
    assert job.file_path == Path(f"/tmp/{response.job_id}.txt")
