"""Run the benchmark questions against strategies A, B and C; write top-3 traces and hit metrics.

Hit definition (GUIDE.md section 4.1): a hit when the chunk covers the gold article
(article_from <= gold <= article_to) AND contains the documented evidence quote.
Hit@1 = top-1 is a hit; Evidence Hit@3 = at least one of the top-3 is a hit.

Strategy C = B's chunks with a chapter metadata filter, applied only to questions
that carry a filter. Questions without a filter run unfiltered under C.

Run from starter/:
    python -m src.retrieve
"""
import json
import re
import time
from pathlib import Path

from .embeddings import E5LocalEmbedder
from .index_chunks import CHROMA_DIR, RESULTS
from .store import ChromaStore

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "benchmark" / "questions.jsonl"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def is_hit(hit: dict, gold_article: int, evidence: str) -> bool:
    m = hit["metadata"]
    covers = m["article_from"] <= gold_article <= m["article_to"]
    return covers and norm(evidence) in norm(hit["text"])


def main() -> None:
    questions = [json.loads(l) for l in QUESTIONS.read_text(encoding="utf-8").splitlines() if l.strip()]
    embedder = E5LocalEmbedder()
    store = ChromaStore(CHROMA_DIR, dimensions=embedder.dimensions)

    summary: dict = {}
    for strategy in ("A", "B", "C"):
        index = "B" if strategy == "C" else strategy
        traces = []
        for q in questions:
            filters = q["filter"] if (strategy == "C" and q["filter"]) else None
            qvec = embedder.embed_query(q["question"])
            t0 = time.perf_counter()
            hits = store.search(index, qvec, top_k=3, filters=filters)
            latency_ms = (time.perf_counter() - t0) * 1000
            flags = [is_hit(h, q["gold_article"], q["evidence_quote"]) for h in hits]
            traces.append({
                "id": q["id"], "split": q["split"], "strategy": strategy,
                "question": q["question"], "filter": filters,
                "gold_article": q["gold_article"],
                "hits": [{"rank": i + 1, "id": h["id"], "score": round(h["score"], 4),
                          "article_from": h["metadata"]["article_from"],
                          "article_to": h["metadata"]["article_to"],
                          "chapter": h["metadata"]["chapter"],
                          "hit": flags[i], "text_preview": h["text"][:160]}
                         for i, h in enumerate(hits)],
                "hit_at_1": bool(flags[:1] and flags[0]),
                "evidence_hit_at_3": any(flags),
                "latency_ms": round(latency_ms, 1),
            })
        with (RESULTS / f"traces_{strategy}.jsonl").open("w", encoding="utf-8") as f:
            for t in traces:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")

        per_split = {}
        for split in ("dev", "test"):
            rows = [t for t in traces if t["split"] == split]
            per_split[split] = {
                "n": len(rows),
                "hit_at_1": f"{sum(t['hit_at_1'] for t in rows)}/{len(rows)}",
                "evidence_hit_at_3": f"{sum(t['evidence_hit_at_3'] for t in rows)}/{len(rows)}",
            }
        summary[strategy] = {
            "per_split": per_split,
            "mean_latency_ms": round(sum(t["latency_ms"] for t in traces) / len(traces), 1),
            "filtered_questions": sum(1 for t in traces if t["filter"]),
        }

    (RESULTS / "retrieval_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
