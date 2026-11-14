"""Chunking strategies for the law corpus.

A (fixed_size): fixed character windows over the whole document, ignoring
    article boundaries. A chunk may span several articles; metadata records every
    article it touches.

B (by_structure): the Điều is the base unit.
    - Điều longer than max_size is split at khoản boundaries, grouping khoản
      greedily up to max_size. A single khoản longer than max_size is split at
      sentence boundaries (flagged as split_level="sentence").
    - Consecutive short Điều (below min_size) in the same chương are merged
      while the merged chunk stays within max_size (article_from != article_to).

C = B chunks + metadata filter on chapter at search time (no separate chunking).
"""
import re
from dataclasses import dataclass

from .models import Chunk, DocumentPage

KHOAN_RE = re.compile(r"^(\d+)\. ", re.M)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;:])\s+")


def _covering_articles(spans: list[tuple[int, int, int]], start: int, end: int) -> list[int]:
    """spans: (article_no, char_start, char_end) in the joined document."""
    return [art for art, s, e in spans if s < end and e > start]


def fixed_size(pages: list[DocumentPage], size: int = 500, overlap: int = 50,
               document_id: str | None = None, source: str | None = None) -> list[Chunk]:
    """Strategy A: sliding character windows over the joined document."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    sep = "\n\n"
    spans: list[tuple[int, int, int]] = []
    parts: list[str] = []
    pos = 0
    for p in pages:
        spans.append((p.page, pos, pos + len(p.text)))
        parts.append(p.text)
        pos += len(p.text) + len(sep)
    full = sep.join(parts)
    doc_id = document_id or pages[0].document_id
    src = source or pages[0].source
    chapter_of = {p.page: p.metadata.get("chapter") for p in pages}

    chunks: list[Chunk] = []
    step = size - overlap
    start = 0
    n = 0
    while start < len(full):
        end = min(start + size, len(full))
        text = full[start:end].strip()
        if text:
            arts = _covering_articles(spans, start, end)
            chapters = sorted({chapter_of[a] for a in arts})
            chunks.append(Chunk(
                chunk_id=f"A-{n:04d}",
                document_id=doc_id,
                source=src,
                page=arts[0],
                text=text,
                metadata={
                    "strategy": "A",
                    "article_from": arts[0],
                    "article_to": arts[-1],
                    "chapter": chapters[0] if len(chapters) == 1 else None,
                    "chapters": chapters,
                    "split_level": "fixed",
                    "chars": len(text),
                },
            ))
            n += 1
        if end == len(full):
            break
        start += step
    return chunks


@dataclass
class _Piece:
    text: str
    article: int
    chapter: str | None
    khoan: str | None
    split_level: str  # "article" | "khoan" | "sentence" | "merged"
    article_to: int | None = None


def _greedy_group(units: list[str], max_size: int, joiner: str) -> list[str]:
    groups: list[str] = []
    cur = ""
    for u in units:
        candidate = u if not cur else cur + joiner + u
        if len(candidate) <= max_size or not cur:
            cur = candidate
        else:
            groups.append(cur)
            cur = u
    if cur:
        groups.append(cur)
    return groups


def _split_article(page: DocumentPage, max_size: int) -> list[_Piece]:
    text = page.text
    if len(text) <= max_size:
        return [_Piece(text, page.page, page.metadata.get("chapter"), None, "article")]

    # Split into khoản. Any intro text before khoản 1 belongs to the first group.
    starts = [m.start() for m in KHOAN_RE.finditer(text)]
    if not starts:
        units = [text]
    else:
        bounds = starts + [len(text)]
        head = text[:starts[0]].rstrip()
        units = [text[starts[i]:bounds[i + 1]].strip() for i in range(len(starts))]
        if head:
            units[0] = head + "\n" + units[0]

    pieces: list[_Piece] = []
    for grp in _greedy_group(units, max_size, "\n"):
        nums = KHOAN_RE.findall(grp)
        label = None
        if nums:
            label = nums[0] if len(nums) == 1 else f"{nums[0]}-{nums[-1]}"
        if len(grp) <= max_size:
            pieces.append(_Piece(grp, page.page, page.metadata.get("chapter"), label, "khoan"))
        else:
            # A single khoản longer than max_size: split at sentences, keep its khoản label.
            for sent_grp in _greedy_group(SENTENCE_SPLIT_RE.split(grp), max_size, " "):
                pieces.append(_Piece(sent_grp, page.page, page.metadata.get("chapter"),
                                     label, "sentence"))
    return pieces


def by_structure(pages: list[DocumentPage], max_size: int = 1500, min_size: int = 400,
                 document_id: str | None = None, source: str | None = None) -> list[Chunk]:
    """Strategy B: Điều as base unit, split to khoản when long, merge when short."""
    pieces: list[_Piece] = []
    for p in pages:
        pieces.extend(_split_article(p, max_size))

    # Merge consecutive short whole-article pieces in the same chương.
    merged: list[_Piece] = []
    for pc in pieces:
        if merged:
            prev = merged[-1]
            same_chapter = prev.chapter == pc.chapter
            both_whole = prev.split_level == "article" and pc.split_level == "article"
            if (both_whole and same_chapter and len(prev.text) < min_size
                    and len(prev.text) + 2 + len(pc.text) <= max_size):
                merged[-1] = _Piece(prev.text + "\n\n" + pc.text, prev.article, prev.chapter,
                                    None, "merged", article_to=pc.article)
                continue
        merged.append(pc)

    doc_id = document_id or pages[0].document_id
    src = source or pages[0].source
    chunks: list[Chunk] = []
    for n, pc in enumerate(merged):
        article_to = pc.article_to if pc.article_to is not None else pc.article
        chunks.append(Chunk(
            chunk_id=f"B-{n:04d}",
            document_id=doc_id,
            source=src,
            page=pc.article,
            text=pc.text,
            metadata={
                "strategy": "B",
                "article_from": pc.article,
                "article_to": article_to,
                "chapter": pc.chapter,
                "chapters": [pc.chapter],
                "khoan": pc.khoan,
                "split_level": pc.split_level,
                "chars": len(pc.text),
            },
        ))
    return chunks
