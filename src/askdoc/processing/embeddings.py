from sentence_transformers import SentenceTransformer

from askdoc.settings import get_settings

_model: SentenceTransformer | None = None


def load_embedding_model() -> None:
    """Load the embedding model once (call from Celery worker_process_init)."""
    global _model
    if _model is None:
        # Force CPU: Celery prefork + PyTorch MPS aborts on macOS (SIGABRT).
        _model = SentenceTransformer(get_settings().embedding_model_name, device="cpu")


def get_embedding_model() -> SentenceTransformer:
    if _model is None:
        load_embedding_model()
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Encode texts into normalized embedding vectors (dim = 384 for MiniLM-L6-v2)."""
    vectors = get_embedding_model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return vectors.tolist()
