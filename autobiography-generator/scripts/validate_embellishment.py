#!/usr/bin/env python3
"""[INFERRED] tag counting + cap enforcement (section 22.3).

Counts [INFERRED] tags in chapter prose and compares the ratio against
the embellishment_cap. Chapters with too many inferred passages risk
departing from source material.

Usage:
    python3 scripts/validate_embellishment.py --chapter-file path/to/ch01.md --cap 0.15
    python3 scripts/validate_embellishment.py --chapter-file path/to/ch01.md

Exit codes:
    0 — within cap
    1 — exceeds cap or file error

P1 Compliance: All validation is deterministic.
SOT Compliance: Read-only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Default embellishment cap (15% of sentences may be inferred).
DEFAULT_CAP: float = 0.15


def count_sentences(text: str) -> int:
    """Count approximate sentences in prose text.

    Ignores markdown headers and horizontal rules. A sentence is defined
    as a span ending with '.', '!', or '?' followed by whitespace or EOF.
    """
    # Strip markdown headers and rules
    lines = text.split("\n")
    content_lines = [
        line for line in lines
        if not line.startswith("#") and line.strip() != "---"
    ]
    content = " ".join(content_lines)

    # Handle common abbreviations to avoid false splits
    content = re.sub(r"\b(Mr|Mrs|Ms|Dr|Prof|Jr|Sr)\.\s", r"\1_DOT_ ", content)

    sentences = re.split(r"[.!?]+(?:\s|$)", content)
    # Filter out empty or trivially short fragments
    return len([s for s in sentences if s.strip() and len(s.strip().split()) >= 3])


def count_inferred_tags(text: str) -> int:
    """Count occurrences of [INFERRED] tags in the text.

    Matches case-insensitive variations: [INFERRED], [Inferred], [inferred].
    """
    return len(re.findall(r"\[INFERRED\]", text, re.IGNORECASE))


def validate_embellishment(chapter_path: Path, cap: float) -> dict:
    """Run embellishment validation on a chapter file.

    Args:
        chapter_path: Path to the chapter markdown file.
        cap: Maximum allowed ratio of inferred sentences (0.0 - 1.0).

    Returns:
        Dictionary with validation results.
    """
    if not chapter_path.is_file():
        return {
            "valid": False,
            "error": f"Chapter file not found: {chapter_path}",
            "inferred_count": 0,
            "sentence_count": 0,
            "ratio": 0.0,
            "cap": cap,
        }

    text = chapter_path.read_text(encoding="utf-8")
    if not text.strip():
        return {
            "valid": False,
            "error": "Chapter file is empty",
            "inferred_count": 0,
            "sentence_count": 0,
            "ratio": 0.0,
            "cap": cap,
        }

    inferred_count = count_inferred_tags(text)
    sentence_count = count_sentences(text)

    if sentence_count == 0:
        ratio = 0.0
    else:
        ratio = inferred_count / sentence_count

    within_cap = ratio <= cap

    return {
        "valid": within_cap,
        "inferred_count": inferred_count,
        "sentence_count": sentence_count,
        "ratio": round(ratio, 4),
        "cap": cap,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate [INFERRED] tag ratio against embellishment cap"
    )
    parser.add_argument(
        "--chapter-file", required=True,
        help="Path to chapter markdown file"
    )
    parser.add_argument(
        "--cap", type=float, default=DEFAULT_CAP,
        help=f"Embellishment cap as decimal (default: {DEFAULT_CAP})"
    )
    args = parser.parse_args()

    chapter_path = Path(args.chapter_file).resolve()
    result = validate_embellishment(chapter_path, args.cap)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    ratio_pct = result["ratio"] * 100
    cap_pct = result["cap"] * 100

    print(f"Embellishment ratio: {ratio_pct:.1f}% (cap: {cap_pct:.1f}%)")
    print(f"  [INFERRED] tags: {result['inferred_count']}")
    print(f"  Total sentences:  {result['sentence_count']}")

    if result["valid"]:
        print("PASS: Within embellishment cap.")
        sys.exit(0)
    else:
        print(
            f"FAIL: Embellishment ratio {ratio_pct:.1f}% exceeds cap {cap_pct:.1f}%.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
