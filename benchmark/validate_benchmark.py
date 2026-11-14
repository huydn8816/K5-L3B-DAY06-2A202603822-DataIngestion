"""Check benchmark questions against the corpus before any retrieval run.

Checks per question:
- gold article exists in the corpus file;
- evidence_quote appears verbatim (whitespace-normalised) inside that article;
- filter (if any) matches the chapter of the gold article;
- question text does not name the gold article number;
- split counts meet the minimum (>=15 dev, >=5 test) and filtered questions (>=3, incl. >=1 test).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "processed" / "luat_19_2023_qh15.normalized.txt"
QUESTIONS = ROOT / "benchmark" / "questions.jsonl"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def article_bodies(text: str) -> dict[int, tuple[str, str]]:
    """Return {article_no: (chapter_roman, body_text)} from the corpus file."""
    chapter = None
    chap_re = re.compile(r"^Chương ([IVX]+)\s*$", re.M)
    art_re = re.compile(r"^Điều (\d+)\. .+$", re.M)
    events = []
    for m in chap_re.finditer(text):
        events.append((m.start(), "chap", m.group(1)))
    for m in art_re.finditer(text):
        events.append((m.start(), "art", int(m.group(1))))
    events.sort()
    out: dict[int, tuple[str, str]] = {}
    for i, (pos, kind, val) in enumerate(events):
        if kind == "chap":
            chapter = val
            continue
        end = events[i + 1][0] if i + 1 < len(events) else len(text)
        out[val] = (chapter, norm(text[pos:end]))
    return out


def main() -> int:
    text = CORPUS.read_text(encoding="utf-8")
    bodies = article_bodies(text)
    rows = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors = []
    for r in rows:
        qid = r["id"]
        art = r["gold_article"]
        if art not in bodies:
            errors.append(f"{qid}: gold article {art} not found in corpus")
            continue
        chapter, body = bodies[art]
        if norm(r["evidence_quote"]) not in body:
            errors.append(f"{qid}: evidence_quote NOT found verbatim in Điều {art}")
        if r["filter"] is not None and r["filter"].get("chapter") != chapter:
            errors.append(f"{qid}: filter chapter {r['filter']} != gold chapter {chapter}")
        if re.search(rf"Điều {art}\b", r["question"]):
            errors.append(f"{qid}: question names the gold article")

    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]
    filt = [r for r in rows if r["filter"] is not None]
    filt_test = [r for r in filt if r["split"] == "test"]
    if len(dev) < 15:
        errors.append(f"dev count {len(dev)} < 15")
    if len(test) < 5:
        errors.append(f"test count {len(test)} < 5")
    if len(filt) < 3:
        errors.append(f"filter questions {len(filt)} < 3")
    if len(filt_test) < 1:
        errors.append("no filter question in test split")

    print(f"questions={len(rows)} dev={len(dev)} test={len(test)} filtered={len(filt)} filtered_test={len(filt_test)}")
    if errors:
        print("FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
