from askdoc.messaging.celery_app import DOCUMENT_INGESTION_TASK, celery_app


@celery_app.task(name=DOCUMENT_INGESTION_TASK)
def process_document(job_id: str, file_name: str, file_path: str) -> None:
    """Process the document ingestion job."""
    print(f"Processing document ingestion job: {job_id} {file_name} {file_path}")
    with open(file_path, encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            print(line.strip())
