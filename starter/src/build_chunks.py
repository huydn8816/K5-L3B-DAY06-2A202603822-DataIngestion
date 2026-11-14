"""Step 3 entry point: normalize the law text and write chunks for strategies A and B.

Run from the starter/ directory:
    python -m src.build_chunks

Outputs:
    data/processed/luat_19_2023_qh15.normalized.txt  (cleaned text used for benchmark checks)
    results/chunks_A.jsonl, results/chunks_B.jsonl    (chunks with metadata, repo root results/)
    results/chunk_stats.json                          (counts, lengths, removed annotations)
"""
import json
import statistics
from collections import Counter
from pathlib import Path

from .chunking import by_structure, fixed_size
from .ingestion import load_law_text, normalize_text, strip_web_annotations
from .models import Chunk

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "luat_19_2023_qh15.txt"
PROCESSED = REPO / "data" / "processed" / "luat_19_2023_qh15.normalized.txt"
RESULTS = Path(__file__).resolve().parents[2] / "results"
DOCUMENT_ID = "luat-19-2023-qh15"
SOURCE = "data/raw/luat_19_2023_qh15.txt"


def _write_chunks(path: Path, chunks: list[Chunk]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "source": c.source,
                "page": c.page,
                "text": c.text,
                "metadata": c.metadata,
            }, ensure_ascii=False) + "\n")


def _length_summary(chunks: list[Chunk]) -> dict:
    lengths = [len(c.text) for c in chunks]
    return {
        "count": len(chunks),
        "min": min(lengths),
        "median": int(statistics.median(lengths)),
        "max": max(lengths),
        "total_chars": sum(lengths),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)

    cleaned, _ = strip_web_annotations(normalize_text(RAW.read_text(encoding="utf-8")))
    PROCESSED.write_text(cleaned + "\n", encoding="utf-8")

    pages, ingest_stats = load_law_text(RAW, DOCUMENT_ID, SOURCE)
    if len(pages) < 30:
        raise SystemExit(f"Only {len(pages)} content units; need at least 30.")

    chunks_a = fixed_size(pages, size=500, overlap=50, document_id=DOCUMENT_ID, source=SOURCE)
    chunks_b = by_structure(pages, max_size=1500, min_size=400, document_id=DOCUMENT_ID, source=SOURCE)
    _write_chunks(RESULTS / "chunks_A.jsonl", chunks_a)
    _write_chunks(RESULTS / "chunks_B.jsonl", chunks_b)

    split_levels = Counter(c.metadata["split_level"] for c in chunks_b)
    multi_article_b = sum(1 for c in chunks_b if c.metadata["article_to"] != c.metadata["article_from"])
    multi_article_a = sum(1 for c in chunks_a if c.metadata["article_to"] != c.metadata["article_from"])
    stats = {
        "corpus_units_articles": len(pages),
        "annotation_removal": dict(ingest_stats),
        "params": {
            "A": {"strategy": "fixed_size", "size": 500, "overlap": 50},
            "B": {"strategy": "by_structure", "max_size": 1500, "min_size": 400},
        },
        "A": {**_length_summary(chunks_a), "chunks_spanning_multiple_articles": multi_article_a},
        "B": {**_length_summary(chunks_b), "chunks_spanning_multiple_articles": multi_article_b,
              "split_level_counts": dict(split_levels)},
    }
    (RESULTS / "chunk_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
