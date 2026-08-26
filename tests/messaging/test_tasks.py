from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from askdoc.messaging.celery_app import DOCUMENT_CHUNKS_TASK
from askdoc.messaging.tasks import process_chunk, process_document


def test_process_document_publishes_one_task_per_chunk(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("Para one.\n\nPara two.", encoding="utf-8")

    mocker.patch(
        "askdoc.messaging.tasks.get_settings",
        return_value=SimpleNamespace(document_chunk_size=12, document_chunk_overlap=0),
    )
    send_task = mocker.patch("askdoc.messaging.tasks.celery_app.send_task")

    process_document.run(
        job_id=str(uuid4()),
        file_name="doc.txt",
        file_path=str(path),
    )

    assert send_task.call_count == 2
    for call in send_task.call_args_list:
        assert call.args[0] == DOCUMENT_CHUNKS_TASK
        kwargs = call.kwargs["kwargs"]
        assert kwargs["file_name"] == "doc.txt"
        assert kwargs["text"] in {"Para one.", "Para two."}
        assert "chunk_id" in kwargs
        assert "job_id" in kwargs
        assert "chunk_index" in kwargs


def test_process_document_raises_when_publish_fails(tmp_path: Path, mocker: MockerFixture) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("Only one paragraph here.", encoding="utf-8")

    mocker.patch(
        "askdoc.messaging.tasks.get_settings",
        return_value=SimpleNamespace(document_chunk_size=500, document_chunk_overlap=0),
    )
    mocker.patch(
        "askdoc.messaging.tasks.celery_app.send_task",
        side_effect=RuntimeError("broker down"),
    )

    with pytest.raises(RuntimeError, match="broker down"):
        process_document.run(
            job_id=str(uuid4()),
            file_name="doc.txt",
            file_path=str(path),
        )


def test_process_chunk_embeds_and_upserts(mocker: MockerFixture) -> None:
    chunk_id = uuid4()
    job_id = uuid4()
    embedding = [0.1, 0.2, 0.3]

    mocker.patch("askdoc.messaging.tasks.embed_texts", return_value=[embedding])
    session = mocker.Mock()
    mocker.patch("askdoc.messaging.tasks.get_session", return_value=session)
    store = mocker.Mock()
    mocker.patch("askdoc.messaging.tasks.PgVectorStore", return_value=store)

    process_chunk.run(
        chunk_id=str(chunk_id),
        job_id=str(job_id),
        file_name="doc.txt",
        chunk_index=2,
        text="chunk text",
    )

    store.upsert.assert_called_once_with(
        chunk_id=chunk_id,
        job_id=job_id,
        file_name="doc.txt",
        chunk_index=2,
        text="chunk text",
        embedding=embedding,
    )
    session.close.assert_called_once()


def test_process_chunk_closes_session_when_upsert_fails(mocker: MockerFixture) -> None:
    mocker.patch("askdoc.messaging.tasks.embed_texts", return_value=[[0.0]])
    session = mocker.Mock()
    mocker.patch("askdoc.messaging.tasks.get_session", return_value=session)
    store = mocker.Mock()
    store.upsert.side_effect = RuntimeError("db error")
    mocker.patch("askdoc.messaging.tasks.PgVectorStore", return_value=store)

    with pytest.raises(RuntimeError, match="db error"):
        process_chunk.run(
            chunk_id=str(uuid4()),
            job_id=str(uuid4()),
            file_name="doc.txt",
            chunk_index=0,
            text="chunk text",
        )

    session.close.assert_called_once()
