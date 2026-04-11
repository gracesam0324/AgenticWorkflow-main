#!/usr/bin/env python3
"""Han-Heung-Jeong (한-흥-정) emotional balance validation (section 22.3).

Korean autobiography narratives balance three emotional currents:
  - 한 (han): sorrow, longing, unresolved grief, perseverance through hardship
  - 흥 (heung): joy, excitement, celebration, collective energy, humor
  - 정 (jeong): affection, bonds, loyalty, warmth, deep interpersonal attachment

This script counts emotion keywords per category in each chapter and compares
against the target emotional_balance from the story bible or config.

Usage:
    python3 scripts/validate_emotional_balance.py --chapter-file path/to/ch01.md --config config/emotion-keywords.yaml
    python3 scripts/validate_emotional_balance.py --chapter-file path/to/ch01.md

Exit codes:
    0 — balanced (no category is severely under- or over-represented)
    1 — severely imbalanced or file error

P1 Compliance: All validation is deterministic.
SOT Compliance: Read-only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


# ──────────────────────────────────────────────
# Default keywords when no config file is provided
# ──────────────────────────────────────────────

DEFAULT_KEYWORDS: dict[str, list[str]] = {
    "han": [
        # Korean
        "한", "슬픔", "눈물", "아픔", "그리움", "외로움", "한스러운",
        "고통", "인내", "참다", "버티다", "견디다", "서러운", "서글픈",
        # English equivalents (for English-language drafts)
        "sorrow", "grief", "longing", "pain", "tears", "endure", "persevere",
        "hardship", "suffering", "yearning", "loss", "ache", "regret",
        "melancholy", "bittersweet", "wistful", "resigned",
    ],
    "heung": [
        # Korean
        "흥", "기쁨", "웃음", "신나는", "축제", "즐거운", "환희",
        "유머", "웃기", "신바람", "축하", "환호", "떠들썩",
        # English equivalents
        "joy", "laughter", "celebration", "excitement", "humor", "delight",
        "festive", "cheerful", "elation", "triumph", "exuberant", "merry",
        "jubilant", "glee", "thrilling", "ecstatic",
    ],
    "jeong": [
        # Korean
        "정", "사랑", "따뜻", "유대", "충성", "우정", "가족",
        "애정", "다정", "정다운", "마음", "보살핌", "어루만지다",
        # English equivalents
        "affection", "bond", "loyalty", "warmth", "devotion", "kinship",
        "tenderness", "care", "embrace", "closeness", "companionship",
        "attachment", "nurture", "cherish", "beloved", "fondness",
    ],
}

# Severe imbalance threshold: if any category's share is below this fraction
# of the expected balanced share, the chapter is considered severely imbalanced.
# With 3 categories, expected share per category is ~33%. Threshold at 10% means
# a category contributing less than 10% of total is a red flag.
DEFAULT_MIN_SHARE: float = 0.10

# If any single category exceeds this fraction, it dominates the chapter.
DEFAULT_MAX_SHARE: float = 0.70


def load_emotion_config(config_path: Path) -> dict[str, Any]:
    """Load emotion keywords and thresholds from a YAML config file.

    Expected format:
        keywords:
          han: [word1, word2, ...]
          heung: [word1, word2, ...]
          jeong: [word1, word2, ...]
        thresholds:
          min_share: 0.10
          max_share: 0.70

    Falls back to defaults for any missing field.
    """
    if not config_path.is_file():
        return {"keywords": DEFAULT_KEYWORDS, "min_share": DEFAULT_MIN_SHARE, "max_share": DEFAULT_MAX_SHARE}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError):
        return {"keywords": DEFAULT_KEYWORDS, "min_share": DEFAULT_MIN_SHARE, "max_share": DEFAULT_MAX_SHARE}

    keywords = data.get("keywords", {})
    for category in ("han", "heung", "jeong"):
        if category not in keywords or not isinstance(keywords[category], list):
            keywords[category] = DEFAULT_KEYWORDS[category]

    thresholds = data.get("thresholds", {})
    min_share = thresholds.get("min_share", DEFAULT_MIN_SHARE)
    max_share = thresholds.get("max_share", DEFAULT_MAX_SHARE)

    return {"keywords": keywords, "min_share": min_share, "max_share": max_share}


def count_emotion_keywords(text: str, keywords: dict[str, list[str]]) -> dict[str, int]:
    """Count occurrences of emotion keywords per category.

    Uses word-boundary matching for English words and substring matching
    for Korean words (Korean has no clear word boundaries).

    Args:
        text: Chapter prose text.
        keywords: Dictionary mapping category names to keyword lists.

    Returns:
        Dictionary mapping category names to occurrence counts.
    """
    counts: dict[str, int] = {}
    text_lower = text.lower()

    for category, word_list in keywords.items():
        total = 0
        for word in word_list:
            word_lower = word.lower()
            # Korean characters: use simple substring count
            if any("\uac00" <= ch <= "\ud7a3" for ch in word_lower):
                total += text_lower.count(word_lower)
            else:
                # English: use word-boundary matching
                pattern = re.compile(r"\b" + re.escape(word_lower) + r"\b", re.IGNORECASE)
                total += len(pattern.findall(text))
        counts[category] = total

    return counts


def assess_balance(
    counts: dict[str, int],
    min_share: float,
    max_share: float,
) -> dict[str, Any]:
    """Assess whether the emotional distribution is balanced.

    Args:
        counts: Keyword counts per category (han, heung, jeong).
        min_share: Minimum acceptable share per category (0.0 - 1.0).
        max_share: Maximum acceptable share per category (0.0 - 1.0).

    Returns:
        Assessment dictionary with shares, verdict, and diagnostics.
    """
    total = sum(counts.values())
    if total == 0:
        return {
            "balanced": True,
            "total_keywords": 0,
            "shares": {k: 0.0 for k in counts},
            "diagnostics": ["No emotion keywords found — chapter may lack emotional depth."],
        }

    shares: dict[str, float] = {}
    for category, count in counts.items():
        shares[category] = round(count / total, 4)

    diagnostics: list[str] = []
    severely_imbalanced = False

    for category, share in shares.items():
        if share < min_share:
            diagnostics.append(
                f"{category} is severely underrepresented: "
                f"{share * 100:.1f}% (minimum: {min_share * 100:.1f}%)"
            )
            severely_imbalanced = True
        elif share > max_share:
            diagnostics.append(
                f"{category} dominates the chapter: "
                f"{share * 100:.1f}% (maximum: {max_share * 100:.1f}%)"
            )
            severely_imbalanced = True

    return {
        "balanced": not severely_imbalanced,
        "total_keywords": total,
        "shares": shares,
        "diagnostics": diagnostics,
    }


def validate_emotional_balance(
    chapter_path: Path,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Run emotional balance validation on a chapter file.

    Args:
        chapter_path: Path to chapter markdown file.
        config_path: Optional path to emotion-keywords.yaml config.

    Returns:
        Dictionary with validation results.
    """
    if not chapter_path.is_file():
        return {
            "valid": False,
            "error": f"Chapter file not found: {chapter_path}",
        }

    text = chapter_path.read_text(encoding="utf-8")
    if not text.strip():
        return {
            "valid": False,
            "error": "Chapter file is empty",
        }

    # Load config (falls back to defaults if no config provided)
    if config_path:
        config = load_emotion_config(config_path)
    else:
        config = {"keywords": DEFAULT_KEYWORDS, "min_share": DEFAULT_MIN_SHARE, "max_share": DEFAULT_MAX_SHARE}

    # Count keywords
    counts = count_emotion_keywords(text, config["keywords"])

    # Assess balance
    assessment = assess_balance(counts, config["min_share"], config["max_share"])

    return {
        "valid": assessment["balanced"],
        "counts": counts,
        "total_keywords": assessment["total_keywords"],
        "shares": assessment["shares"],
        "diagnostics": assessment["diagnostics"],
        "thresholds": {
            "min_share": config["min_share"],
            "max_share": config["max_share"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate han-heung-jeong emotional balance in a chapter"
    )
    parser.add_argument(
        "--chapter-file", required=True,
        help="Path to chapter markdown file"
    )
    parser.add_argument(
        "--config", default=None,
        help="Path to emotion-keywords.yaml config (default: built-in keywords)"
    )
    args = parser.parse_args()

    chapter_path = Path(args.chapter_file).resolve()
    config_path = Path(args.config).resolve() if args.config else None

    result = validate_emotional_balance(chapter_path, config_path)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Print per-category counts
    counts = result["counts"]
    shares = result["shares"]
    total = result["total_keywords"]

    print("Emotional Balance Report")
    print("=" * 40)
    print(f"  han (sorrow/longing):   {counts.get('han', 0):4d}  ({shares.get('han', 0) * 100:5.1f}%)")
    print(f"  heung (joy/energy):     {counts.get('heung', 0):4d}  ({shares.get('heung', 0) * 100:5.1f}%)")
    print(f"  jeong (affection/bond): {counts.get('jeong', 0):4d}  ({shares.get('jeong', 0) * 100:5.1f}%)")
    print(f"  Total keywords:         {total:4d}")
    print("=" * 40)

    if result["diagnostics"]:
        print("\nDiagnostics:")
        for diag in result["diagnostics"]:
            print(f"  - {diag}")

    if result["valid"]:
        print("\nPASS: Emotional balance is within acceptable range.")
        sys.exit(0)
    else:
        print(
            "\nFAIL: Severe emotional imbalance detected.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
