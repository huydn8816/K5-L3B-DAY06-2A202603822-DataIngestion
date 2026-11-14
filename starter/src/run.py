"""Single entry point for the Day 06 pipeline (run from starter/).

    python -m src.run                  # build chunks -> index -> retrieval
    python -m src.run --with-manual    # also regenerate manual-assessment sheets

Manual sheets are optional because regenerating them changes the blinded row codes;
only regenerate when the labels are being redone (see RUN_LOCAL.md).
"""
import sys

from . import build_chunks, index_chunks, prepare_manual_sheets, retrieve


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    steps = [
        ("1. chunk A and B", build_chunks.main),
        ("2. embed and index in Chroma", index_chunks.main),
        ("3. retrieval and hit metrics", retrieve.main),
    ]
    if "--with-manual" in argv:
        steps.append(("4. manual-assessment sheets", prepare_manual_sheets.main))
    for name, fn in steps:
        print(f"== {name}", flush=True)
        fn()


if __name__ == "__main__":
    main()
