"""Prepare the manual-assessment sheets (coherence, metadata, grounding).

Sampling rules are fixed here, before any manual label exists:
- Coherence positions: articles 1, 9, 17, ..., 73 (every 8th article, 10 positions).
  For each strategy, the chunks that contain the first 40 characters of that article.
- Metadata audit: all 6 test questions x top-3 hits, for A, B and C.
  Automatic check (to be confirmed manually): every "Điều N." heading inside the chunk
  lies within [article_from, article_to] and the chapter matches the headings.
- Grounding: all 6 test questions x top-3 hits, for A, B and C (one label per
  question-strategy pair, judged on the top-3 text together).
- Strategy names are hidden with random row codes (seeded). The key is kept in a
  separate file, opened only after labelling.

Run from starter/:
    python -m src.prepare_manual_sheets
"""
import csv
import json
import random
import re
from pathlib import Path

from .ingestion import load_law_text
from .index_chunks import RESULTS
from .models import Chunk

REPO = Path(__file__).resolve().parents[2]
MANUAL = RESULTS / "manual"
CORPUS = REPO / "data" / "raw" / "luat_19_2023_qh15.txt"
SEED = 20261114


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    MANUAL.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    pages, _ = load_law_text(CORPUS, "luat-19-2023-qh15", "data/raw/luat_19_2023_qh15.txt")
    page_by_no = {p.page: p for p in pages}
    chunks = {s: read_jsonl(RESULTS / f"chunks_{s}.jsonl") for s in ("A", "B")}
    traces = {s: {t["id"]: t for t in read_jsonl(RESULTS / f"traces_{s}.jsonl")} for s in ("A", "B", "C")}
    key: dict[str, dict] = {}

    def code(prefix: str, n: int) -> list[str]:
        codes = [f"{prefix}{i:03d}" for i in range(1, n + 1)]
        rng.shuffle(codes)
        return codes

    # 1. Coherence -------------------------------------------------------------
    positions = list(range(1, 81, 8))  # 1, 9, ..., 73
    coherence_rows = []
    for art in positions:
        head = norm(page_by_no[art].text)[:40]
        for strat in ("A", "B"):
            covering = [c for c in chunks[strat] if head in norm(c["text"])]
            if not covering:
                covering = [{"chunk_id": "NOT_FOUND", "text": "", "metadata": {}}]
            for c in covering:
                coherence_rows.append({"article": art, "strategy": strat,
                                       "chunk_id": c["chunk_id"], "text": c["text"]})
    codes = code("CO", len(coherence_rows))
    csv_rows = []
    for r, cd in zip(coherence_rows, codes):
        key[cd] = {"sheet": "coherence", "strategy": r["strategy"], "article": r["article"], "chunk_id": r["chunk_id"]}
        csv_rows.append({"row": cd, "chunk_text": r["text"], "score_0_2": "", "reason": ""})
    write_csv(MANUAL / "coherence_sheet.csv", csv_rows)

    # 2. Metadata audit --------------------------------------------------------
    meta_rows = []
    for qid in [q for q, t in traces["A"].items() if t["split"] == "test"]:
        for strat in ("A", "B", "C"):
            for h in traces[strat][qid]["hits"]:
                src_chunks = chunks["B" if strat == "C" else strat]
                text = next(c["text"] for c in src_chunks if c["chunk_id"] == h["id"].split(":")[-1])
                # Auto check: the chunk text must appear inside the articles named in its metadata,
                # and every article in that range must belong to the recorded chapter(s).
                span = range(h["article_from"], h["article_to"] + 1)
                body = norm("\n".join(page_by_no[n].text for n in span))
                in_range = norm(text) in body
                chapters_in_span = {page_by_no[n].metadata["chapter"] for n in span}
                chapter_ok = (h["chapter"] in chapters_in_span) if h["chapter"] else (len(chapters_in_span) > 1)
                auto_ok = in_range and chapter_ok
                filt = traces[strat][qid]["filter"]
                filter_ok = None
                if filt is not None:
                    filter_ok = h["chapter"] == filt["chapter"]
                meta_rows.append({"question": qid, "strategy": strat, "rank": h["rank"], "chunk_id": h["id"],
                                  "article_from": h["article_from"], "article_to": h["article_to"],
                                  "chapter": h["chapter"], "auto_check_passed": auto_ok,
                                  "filter_compliant": "N/A" if filt is None else filter_ok,
                                  "manual_source_ok": "", "manual_article_ok": "", "manual_chapter_ok": "",
                                  "note": ""})
    codes = code("MD", len(meta_rows))
    csv_rows = []
    for r, cd in zip(meta_rows, codes):
        key[cd] = {"sheet": "metadata", "strategy": r["strategy"], "question": r["question"],
                   "rank": r["rank"], "chunk_id": r["chunk_id"]}
        csv_rows.append({"row": cd, **{k: v for k, v in r.items() if k not in ("strategy", "question", "rank", "chunk_id")}})
    write_csv(MANUAL / "metadata_sheet.csv", csv_rows)

    # 3. Grounding -------------------------------------------------------------
    ground_rows = []
    for qid in [q for q, t in traces["A"].items() if t["split"] == "test"]:
        for strat in ("A", "B", "C"):
            t = traces[strat][qid]
            top3 = "\n---\n".join(
                f"[rank {h['rank']} | Điều {h['article_from']}-{h['article_to']}]\n" +
                next(c["text"] for c in chunks["B" if strat == "C" else strat] if c["chunk_id"] == h["id"].split(":")[-1])
                for h in t["hits"])
            ground_rows.append({"question": qid, "strategy": strat, "question_text": t["question"],
                                "top3_text": top3})
    codes = code("GR", len(ground_rows))
    csv_rows = []
    for r, cd in zip(ground_rows, codes):
        key[cd] = {"sheet": "grounding", "strategy": r["strategy"], "question": r["question"]}
        csv_rows.append({"row": cd, "question_text": r["question_text"], "top3_text": r["top3_text"],
                         "grade_0_1_2": "", "reason": ""})
    write_csv(MANUAL / "grounding_sheet.csv", csv_rows)

    (MANUAL / "KEY_do_not_open_until_labelled.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"coherence_rows": len(coherence_rows), "metadata_rows": len(meta_rows),
                      "grounding_rows": len(ground_rows),
                      "metadata_auto_check_failed": sum(1 for r in meta_rows if not r["auto_check_passed"]),
                      "filter_violations": sum(1 for r in meta_rows if r["filter_compliant"] is False)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
