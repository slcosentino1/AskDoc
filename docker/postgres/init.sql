CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunk_embeddings (
    chunk_id UUID PRIMARY KEY,
    job_id UUID NOT NULL,
    file_name TEXT NOT NULL,
    chunk_index INT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, chunk_index)
);

CREATE INDEX idx_document_chunk_embeddings_hnsw
ON document_chunk_embeddings USING hnsw (embedding vector_cosine_ops);