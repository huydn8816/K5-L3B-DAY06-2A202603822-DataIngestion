"""Local persistent vector store with Chroma (cosine similarity, metadata filters).

Docker/PostgreSQL is not available on the lab machine, so the store is Chroma in
local persistent mode. One collection per strategy (law_A, law_B) so the three
configurations are stored separately but with the same embedder.

Re-ingest rules:
- ids are deterministic ("<document_id>:<chunk_id>"), so re-upserting the same
  chunks does not duplicate them;
- chunks that disappeared from the source are deleted.
"""
from pathlib import Path
from typing import Any

from .models import Chunk

COLLECTION_PREFIX = "law"


def _scalar_metadata(chunk: Chunk) -> dict[str, Any]:
    """Chroma metadata must be scalar; flatten lists and drop None."""
    m = chunk.metadata
    out: dict[str, Any] = {
        "document_id": chunk.document_id,
        "source": chunk.source,
        "page": int(chunk.page),
        "article_from": int(m["article_from"]),
        "article_to": int(m["article_to"]),
        "chapter": m.get("chapter") or "",
        "chapters": ",".join(c for c in m.get("chapters", []) if c),
        "split_level": m.get("split_level", ""),
        "khoan": m.get("khoan") or "",
        "chunk_id": chunk.chunk_id,
    }
    return out


class ChromaStore:
    def __init__(self, persist_dir: Path, dimensions: int) -> None:
        import chromadb

        self.dimensions = dimensions
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))

    def _collection(self, strategy: str):
        return self._client.get_or_create_collection(
            name=f"{COLLECTION_PREFIX}_{strategy}",
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> dict[str, int]:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        for v in vectors:
            if len(v) != self.dimensions:
                raise ValueError(f"vector has {len(v)} dims, store expects {self.dimensions}")
        col = self._collection(strategy)
        ids = [f"{c.document_id}:{c.chunk_id}" for c in chunks]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate chunk ids in input")

        existing = set(col.get(include=[])["ids"])
        obsolete = sorted(existing - set(ids))
        if obsolete:
            col.delete(ids=obsolete)

        col.upsert(
            ids=ids,
            embeddings=vectors,
            documents=[c.text for c in chunks],
            metadatas=[_scalar_metadata(c) for c in chunks],
        )
        return {"upserted": len(ids), "deleted_obsolete": len(obsolete), "total": col.count()}

    def count(self, strategy: str) -> int:
        return self._collection(strategy).count()

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Return top-k hits: chunk id, text, cosine distance, score and metadata."""
        if len(query_vector) != self.dimensions:
            raise ValueError("query vector dimension mismatch")
        col = self._collection(strategy)
        kwargs: dict[str, Any] = {"query_embeddings": [query_vector], "n_results": top_k}
        if filters:
            kwargs["where"] = {k: v for k, v in filters.items()}
        res = col.query(**kwargs)
        hits = []
        for i, cid in enumerate(res["ids"][0]):
            dist = res["distances"][0][i]
            hits.append({
                "id": cid,
                "text": res["documents"][0][i],
                "distance": dist,
                "score": 1.0 - dist,
                "metadata": res["metadatas"][0][i],
            })
        return hits
