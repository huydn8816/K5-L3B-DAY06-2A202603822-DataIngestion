"""Read and normalize source data.

Implemented for the chosen corpus: Luật 19/2023/QH15 extracted as plain text
(data/raw/luat_19_2023_qh15.txt). Each Điều becomes one DocumentPage whose
page number is the article number and whose metadata carries the chapter.

load_pdf is kept as a stub: the corpus is text, not PDF.
"""
import re
import unicodedata
from collections import Counter
from pathlib import Path

from .models import DocumentPage

# Website annotations found inside the extracted text (see benchmark/README.md).
# Each rule: (name, predicate on a stripped line) -> True means drop the line.
_DROP_RULES = [
    ("data_href_fragment", lambda s: "data-href" in s),
    ("replacement_note", lambda s: re.match(r"^Cụm từ .*(bị thay thế|bị bãi bỏ|được sửa đổi|được bổ sung) bởi", s) is not None),
    ("guidance_note", lambda s: "được hướng dẫn bởi" in s),
    ("decree_ref", lambda s: re.match(r"^(?:khoản \d+ )?Điều \d+ Nghị định 146/2025/NĐ-CP$", s) is not None),
    ("effective_window_note", lambda s: re.match(r"^, áp dụng từ ngày .* 28/02/2027\.$", s) is not None),
    ("task_note", lambda s: re.match(r"^Nhiệm vụ, quyền hạn của .* quy định chi tiết", s) is not None),
]

ARTICLE_RE = re.compile(r"^Điều (\d+)\. (.+)$")
CHAPTER_RE = re.compile(r"^Chương ([IVX]+)$")


def normalize_text(text: str) -> str:
    """Unicode NFC, unify line endings, collapse horizontal whitespace."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(lines)


def strip_web_annotations(text: str) -> tuple[str, Counter]:
    """Remove website annotation lines. Returns cleaned text and per-rule counts."""
    stats: Counter = Counter()
    lines = text.split("\n")
    # A label line that directly precedes a link tag is an annotation too.
    link_idx = {i for i, ln in enumerate(lines) if "data-href" in ln}
    out: list[str] = []
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s:
            continue
        if (i + 1) in link_idx and "data-href" not in s:
            stats["link_label"] += 1
            continue
        if s.startswith('"> '):
            # Inline amendment fragment: keep the wording, drop the markup.
            s = s[3:].strip()
            stats["quote_marker_stripped"] += 1
            if not s:
                continue
        dropped = False
        for name, pred in _DROP_RULES:
            if pred(s):
                stats[name] += 1
                dropped = True
                break
        if not dropped:
            out.append(s)
    return "\n".join(out), stats


def load_law_text(path: Path, document_id: str, source: str) -> tuple[list[DocumentPage], Counter]:
    """Return one DocumentPage per Điều, plus annotation-removal statistics."""
    raw = path.read_text(encoding="utf-8")
    cleaned, stats = strip_web_annotations(normalize_text(raw))
    pages: list[DocumentPage] = []
    chapter = None
    chapter_title = None
    current: DocumentPage | None = None
    lines = cleaned.split("\n")
    for i, line in enumerate(lines):
        ch = CHAPTER_RE.match(line)
        if ch:
            chapter = ch.group(1)
            chapter_title = lines[i + 1] if i + 1 < len(lines) else ""
            current = None
            continue
        art = ARTICLE_RE.match(line)
        if art:
            current = DocumentPage(
                document_id=document_id,
                source=source,
                page=int(art.group(1)),
                text=line,
                metadata={
                    "chapter": chapter,
                    "chapter_title": chapter_title,
                    "article_title": art.group(2),
                },
            )
            pages.append(current)
            continue
        if current is not None:
            current.text += "\n" + line
    stats["articles"] = len(pages)
    return pages, stats


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Not used: the chosen corpus is text. Kept as the starter contract."""
    raise NotImplementedError("PDF loading is not needed for the text corpus")
