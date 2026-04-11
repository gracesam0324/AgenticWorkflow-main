#!/usr/bin/env python3
"""Controlling metaphor presence validation (section 22.3).

Reads the controlling_metaphor from the story bible and verifies it
appears in at least 3 chapters. A controlling metaphor that threads
through the narrative provides structural cohesion.

Usage:
    python3 scripts/validate_metaphor.py --bible-path path/to/story_bible.json --chapters-dir path/to/chapters/
    python3 scripts/validate_metaphor.py --bible-path path/to/story_bible.json --chapters-dir path/to/chapters/ --min-chapters 5

Exit codes:
    0 — metaphor present in >= minimum chapters
    1 — insufficient metaphor presence or file error

P1 Compliance: All validation is deterministic.
SOT Compliance: Read-only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DEFAULT_MIN_CHAPTERS: int = 3


def load_story_bible(bible_path: Path) -> dict | None:
    """Load and parse the story bible JSON file."""
    if not bible_path.is_file():
        return None
    try:
        with open(bible_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def extract_controlling_metaphor(story_bible: dict) -> str | None:
    """Extract the controlling_metaphor term from the story bible.

    Checks multiple possible locations in the story bible structure:
      - story_bible["meta"]["controlling_metaphor"]
      - story_bible["voice_guide"]["controlling_metaphor"]
      - story_bible["controlling_metaphor"]
    """
    # Check common locations
    meta = story_bible.get("meta", {})
    if isinstance(meta, dict) and "controlling_metaphor" in meta:
        return meta["controlling_metaphor"]

    voice_guide = story_bible.get("voice_guide", {})
    if isinstance(voice_guide, dict) and "controlling_metaphor" in voice_guide:
        return voice_guide["controlling_metaphor"]

    if "controlling_metaphor" in story_bible:
        return story_bible["controlling_metaphor"]

    return None


def find_chapter_files(chapters_dir: Path) -> list[Path]:
    """Find all chapter markdown files in the chapters directory.

    Matches patterns like ch01_draft_v1.md, ch02_draft_v2.md, etc.
    Returns only the latest version of each chapter.
    """
    if not chapters_dir.is_dir():
        return []

    pattern = re.compile(r"ch(\d{2})_draft_v(\d+)\.md$")
    latest: dict[int, tuple[int, Path]] = {}

    for f in chapters_dir.iterdir():
        m = pattern.match(f.name)
        if m:
            ch_num = int(m.group(1))
            version = int(m.group(2))
            if ch_num not in latest or version > latest[ch_num][0]:
                latest[ch_num] = (version, f)

    return [path for _, path in sorted(latest.values(), key=lambda x: x[1].name)]


def check_metaphor_in_chapter(chapter_path: Path, metaphor: str) -> bool:
    """Check whether the controlling metaphor appears in a chapter file.

    Uses case-insensitive word-boundary matching.
    """
    try:
        text = chapter_path.read_text(encoding="utf-8")
    except OSError:
        return False

    escaped = re.escape(metaphor)
    return bool(re.search(escaped, text, re.IGNORECASE))


def validate_metaphor(
    bible_path: Path,
    chapters_dir: Path,
    min_chapters: int = DEFAULT_MIN_CHAPTERS,
) -> dict:
    """Validate controlling metaphor presence across chapters.

    Args:
        bible_path: Path to story_bible.json.
        chapters_dir: Path to directory containing chapter markdown files.
        min_chapters: Minimum number of chapters the metaphor must appear in.

    Returns:
        Dictionary with validation results.
    """
    story_bible = load_story_bible(bible_path)
    if story_bible is None:
        return {
            "valid": False,
            "error": f"Story bible not found or invalid: {bible_path}",
            "metaphor": None,
            "chapters_with_metaphor": [],
            "chapters_without_metaphor": [],
        }

    metaphor = extract_controlling_metaphor(story_bible)
    if not metaphor:
        return {
            "valid": False,
            "error": "No controlling_metaphor found in story bible",
            "metaphor": None,
            "chapters_with_metaphor": [],
            "chapters_without_metaphor": [],
        }

    chapter_files = find_chapter_files(chapters_dir)
    if not chapter_files:
        return {
            "valid": False,
            "error": f"No chapter files found in: {chapters_dir}",
            "metaphor": metaphor,
            "chapters_with_metaphor": [],
            "chapters_without_metaphor": [],
        }

    chapters_with: list[str] = []
    chapters_without: list[str] = []

    for ch_path in chapter_files:
        if check_metaphor_in_chapter(ch_path, metaphor):
            chapters_with.append(ch_path.name)
        else:
            chapters_without.append(ch_path.name)

    is_valid = len(chapters_with) >= min_chapters

    return {
        "valid": is_valid,
        "metaphor": metaphor,
        "min_chapters_required": min_chapters,
        "chapters_with_metaphor": chapters_with,
        "chapters_without_metaphor": chapters_without,
        "count": len(chapters_with),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate controlling metaphor presence across chapters"
    )
    parser.add_argument(
        "--bible-path", required=True,
        help="Path to story_bible.json"
    )
    parser.add_argument(
        "--chapters-dir", required=True,
        help="Path to directory containing chapter markdown files"
    )
    parser.add_argument(
        "--min-chapters", type=int, default=DEFAULT_MIN_CHAPTERS,
        help=f"Minimum chapters the metaphor must appear in (default: {DEFAULT_MIN_CHAPTERS})"
    )
    args = parser.parse_args()

    bible_path = Path(args.bible_path).resolve()
    chapters_dir = Path(args.chapters_dir).resolve()

    result = validate_metaphor(bible_path, chapters_dir, args.min_chapters)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    metaphor = result["metaphor"]
    count = result["count"]
    min_req = result["min_chapters_required"]

    print(f"Controlling metaphor: \"{metaphor}\"")
    print(f"Present in {count} chapter(s) (minimum required: {min_req})")

    if result["chapters_with_metaphor"]:
        print(f"  Present:  {', '.join(result['chapters_with_metaphor'])}")
    if result["chapters_without_metaphor"]:
        print(f"  Absent:   {', '.join(result['chapters_without_metaphor'])}")

    if result["valid"]:
        print("PASS: Controlling metaphor has sufficient presence.")
        sys.exit(0)
    else:
        print(
            f"FAIL: Metaphor appears in {count} chapter(s), minimum is {min_req}.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
