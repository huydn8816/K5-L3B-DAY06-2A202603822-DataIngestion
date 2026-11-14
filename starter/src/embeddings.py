"""Local embedding with intfloat/multilingual-e5-small (pinned revision).

No mock fallback: if the model cannot load or returns bad vectors, the error is raised.
E5 models expect the prefixes "passage: " for indexed text and "query: " for questions.
"""
import math
from typing import Protocol

MODEL_NAME = "intfloat/multilingual-e5-small"
MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
EXPECTED_DIMENSIONS = 384


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class E5LocalEmbedder:
    """Adapter around sentence-transformers for multilingual-e5-small."""

    def __init__(self, model_name: str = MODEL_NAME, revision: str = MODEL_REVISION) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.revision = revision
        self._model = SentenceTransformer(model_name, revision=revision, device="cpu")
        getter = getattr(self._model, "get_embedding_dimension", None) or self._model.get_sentence_embedding_dimension
        self.dimensions = getter()
        if self.dimensions != EXPECTED_DIMENSIONS:
            raise RuntimeError(f"expected {EXPECTED_DIMENSIONS} dims, model reports {self.dimensions}")

    def _encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(
            texts, batch_size=16, normalize_embeddings=True, convert_to_numpy=True,
            show_progress_bar=False,
        )
        out = [[float(x) for x in v] for v in vectors]
        for v in out:
            if len(v) != self.dimensions or any(math.isnan(x) or math.isinf(x) for x in v):
                raise RuntimeError("embedding returned invalid vector")
        return out

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode([f"passage: {t}" for t in texts])

    def embed_query(self, question: str) -> list[float]:
        return self._encode([f"query: {question}"])[0]
