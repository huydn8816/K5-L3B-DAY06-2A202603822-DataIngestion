"""Embed chunks for strategies A and B and store them in local Chroma.

Run from starter/:
    python -m src.index_chunks

Runs the upsert twice on purpose and prints both results: the second run must
report 0 new vectors and an unchanged total (no duplicates).
"""
import json
from pathlib import Path

from .embeddings import E5LocalEmbedder
from .models import Chunk
from .store import ChromaStore

RESULTS = Path(__file__).resolve().parents[2] / "results"
CHROMA_DIR = RESULTS / "chroma"


def load_chunks(path: Path) -> list[Chunk]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        out.append(Chunk(
            chunk_id=r["chunk_id"], document_id=r["document_id"], source=r["source"],
            page=r["page"], text=r["text"], metadata=r["metadata"],
        ))
    return out


def main() -> None:
    embedder = E5LocalEmbedder()
    store = ChromaStore(CHROMA_DIR, dimensions=embedder.dimensions)
    summary = {"model": embedder.model_name, "revision": embedder.revision,
               "dimensions": embedder.dimensions, "runs": {}}
    for strategy in ("A", "B"):
        chunks = load_chunks(RESULTS / f"chunks_{strategy}.jsonl")
        vectors = embedder.embed_documents([c.text for c in chunks])
        first = store.upsert(strategy, chunks, vectors)
        second = store.upsert(strategy, chunks, vectors)  # re-ingest check
        summary["runs"][strategy] = {"chunks": len(chunks), "first_run": first, "second_run": second}
    (RESULTS / "index_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
