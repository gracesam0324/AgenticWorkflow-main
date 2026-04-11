#!/usr/bin/env python3
"""
check.py — Quick Quality Check for Autobiography Chapters
Runs in <5 seconds. Outputs pass/fail per check.

Usage:
    python3 scripts/check.py outputs/chapters/chapter-01.md
    python3 scripts/check.py outputs/chapters/           # check all chapters
    python3 scripts/check.py outputs/drafts/chapter-writer-*.md --source test-data/micro-interviews/INT-001-childhood.json
    python3 scripts/check.py outputs/chapters/ --json     # machine-readable output

Checks:
    1. Word count per chapter (target: 3500-5000)
    2. Name consistency across chapters
    3. Timeline chronology validation
    4. Readability score (Flesch-Kincaid)
    5. Quote grounding (quotes must appear in source transcripts)
    6. Structural checks (headings, paragraphs, scene openings)
"""

import sys
import os
import re
import json
import math
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional

# ---------------------------------------------------------------------------
# Readability: inline Flesch-Kincaid (no external dependency required)
# If textstat is installed, we use it. Otherwise, fallback to manual calc.
# ---------------------------------------------------------------------------
try:
    import textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False


def count_syllables(word: str) -> int:
    """Estimate syllable count for English words."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    word = re.sub(r'(?:[^leas]ed|[^aeiou]e)$', '', word)
    word = re.sub(r'^re', 're', word)
    vowels = re.findall(r'[aeiouy]+', word)
    return max(1, len(vowels))


def flesch_kincaid_grade(text: str) -> float:
    """Calculate Flesch-Kincaid Grade Level."""
    if HAS_TEXTSTAT:
        return textstat.flesch_kincaid_grade(text)

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r'\b[a-zA-Z]+\b', text)

    if not sentences or not words:
        return 0.0

    total_sentences = len(sentences)
    total_words = len(words)
    total_syllables = sum(count_syllables(w) for w in words)

    grade = (0.39 * (total_words / total_sentences) +
             11.8 * (total_syllables / total_words) - 15.59)
    return round(grade, 1)


def flesch_reading_ease(text: str) -> float:
    """Calculate Flesch Reading Ease score."""
    if HAS_TEXTSTAT:
        return textstat.flesch_reading_ease(text)

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r'\b[a-zA-Z]+\b', text)

    if not sentences or not words:
        return 0.0

    total_sentences = len(sentences)
    total_words = len(words)
    total_syllables = sum(count_syllables(w) for w in words)

    ease = (206.835 - 1.015 * (total_words / total_sentences) -
            84.6 * (total_syllables / total_words))
    return round(ease, 1)


# ---------------------------------------------------------------------------
# Check 1: Word Count
# ---------------------------------------------------------------------------
def check_word_count(text: str, min_words: int = 3500, max_words: int = 5000) -> dict:
    words = text.split()
    count = len(words)
    passed = min_words <= count <= max_words

    detail = f"{count} words"
    if count < min_words:
        detail += f" (SHORT: need {min_words - count} more)"
    elif count > max_words:
        detail += f" (LONG: {count - max_words} over)"
    else:
        detail += f" (in range {min_words}-{max_words})"

    return {
        "check": "word_count",
        "passed": passed,
        "value": count,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# Check 2: Name Consistency
# ---------------------------------------------------------------------------
def check_name_consistency(texts: list[tuple[str, str]],
                           known_names: Optional[list[str]] = None) -> dict:
    """
    Check that names are spelled consistently across all chapters.
    texts: list of (filename, text_content) tuples
    known_names: list of canonical names from transcripts
    """
    issues = []

    # Extract capitalized name-like tokens (2+ capital-letter words in sequence)
    all_names = Counter()
    per_file_names: dict[str, set] = {}

    for fname, text in texts:
        # Find potential names: sequences of capitalized words
        name_candidates = re.findall(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text
        )
        file_names = set(name_candidates)
        per_file_names[fname] = file_names
        for name in name_candidates:
            all_names[name] += 1

    # Check for near-duplicate names (potential misspellings)
    name_list = list(all_names.keys())
    for i, name_a in enumerate(name_list):
        for name_b in name_list[i + 1:]:
            # Simple similarity: share a word but differ
            words_a = set(name_a.lower().split())
            words_b = set(name_b.lower().split())
            if words_a & words_b and words_a != words_b:
                # They share a name component but aren't identical
                issues.append(
                    f"Possible inconsistency: '{name_a}' vs '{name_b}'"
                )

    # Check against known canonical names
    if known_names:
        for canonical in known_names:
            found = False
            for name in all_names:
                if canonical.lower() in name.lower() or name.lower() in canonical.lower():
                    found = True
                    break
            if not found:
                # Not necessarily an issue, but flag
                pass

    passed = len(issues) == 0
    return {
        "check": "name_consistency",
        "passed": passed,
        "value": len(issues),
        "detail": "; ".join(issues[:5]) if issues else "All names consistent",
        "names_found": dict(all_names.most_common(20)),
    }


# ---------------------------------------------------------------------------
# Check 3: Timeline Chronology
# ---------------------------------------------------------------------------
def check_timeline(text: str) -> dict:
    """Check that years mentioned are in roughly chronological order."""
    # Find all 4-digit years in the text
    years = re.findall(r'\b(19\d{2}|20[0-2]\d)\b', text)
    years_int = [int(y) for y in years]

    if len(years_int) < 2:
        return {
            "check": "timeline_chronology",
            "passed": True,
            "value": len(years_int),
            "detail": f"Only {len(years_int)} year(s) found, skipping chronology check",
        }

    # Check if years are mostly non-decreasing (allowing some flashbacks)
    violations = 0
    violation_details = []
    for i in range(1, len(years_int)):
        if years_int[i] < years_int[i - 1] - 5:  # Allow small jumps (context)
            violations += 1
            if len(violation_details) < 3:
                violation_details.append(
                    f"Year {years_int[i]} appears after {years_int[i-1]}"
                )

    # Tolerate up to 20% violations (flashbacks are legitimate)
    threshold = max(1, len(years_int) // 5)
    passed = violations <= threshold

    return {
        "check": "timeline_chronology",
        "passed": passed,
        "value": violations,
        "detail": (
            f"{violations} chronology jumps in {len(years_int)} year refs. "
            + ("; ".join(violation_details) if violation_details else "OK")
        ),
        "years_sequence": years_int[:20],
    }


# ---------------------------------------------------------------------------
# Check 4: Readability
# ---------------------------------------------------------------------------
def check_readability(text: str) -> dict:
    """Readability should be grade 6-12 for autobiography (accessible but literary)."""
    grade = flesch_kincaid_grade(text)
    ease = flesch_reading_ease(text)

    passed = 6.0 <= grade <= 12.0

    ease_label = "very easy"
    if ease < 30:
        ease_label = "very difficult"
    elif ease < 50:
        ease_label = "difficult"
    elif ease < 60:
        ease_label = "fairly difficult"
    elif ease < 70:
        ease_label = "standard"
    elif ease < 80:
        ease_label = "fairly easy"
    elif ease < 90:
        ease_label = "easy"

    return {
        "check": "readability",
        "passed": passed,
        "value": grade,
        "detail": f"FK Grade: {grade}, Reading Ease: {ease} ({ease_label})",
    }


# ---------------------------------------------------------------------------
# Check 5: Quote Grounding
# ---------------------------------------------------------------------------
def check_quote_grounding(text: str, source_file: Optional[str] = None) -> dict:
    """Verify that direct quotes in the chapter appear in source transcripts."""
    # Extract quoted text from the chapter
    chapter_quotes = re.findall(r'["\u201c]([^"\u201d]{10,})["\u201d]', text)

    if not chapter_quotes:
        return {
            "check": "quote_grounding",
            "passed": True,
            "value": 0,
            "detail": "No direct quotes found in text",
        }

    if not source_file or not os.path.exists(source_file):
        return {
            "check": "quote_grounding",
            "passed": True,  # Can't verify without source
            "value": len(chapter_quotes),
            "detail": f"{len(chapter_quotes)} quotes found, no source file to verify against",
        }

    # Load source transcript
    with open(source_file) as f:
        source_data = json.load(f)

    # Collect all text from source
    source_text = ""
    source_quotes = []
    for seg in source_data.get("segments", []):
        source_text += " " + seg.get("content", "")
        for kq in seg.get("key_quotes", []):
            source_quotes.append(kq["text"].lower().strip())

    source_text_lower = source_text.lower()

    # Check each chapter quote
    grounded = 0
    ungrounded = []
    for q in chapter_quotes:
        q_lower = q.lower().strip().rstrip('.,!?')
        # Check if the quote (or a substantial substring) appears in source
        if q_lower in source_text_lower:
            grounded += 1
        elif any(q_lower in sq or sq in q_lower for sq in source_quotes):
            grounded += 1
        else:
            # Check partial match (at least 60% of words)
            q_words = set(q_lower.split())
            source_words = set(source_text_lower.split())
            overlap = len(q_words & source_words) / max(len(q_words), 1)
            if overlap > 0.6:
                grounded += 1
            else:
                ungrounded.append(q[:50] + "..." if len(q) > 50 else q)

    total = len(chapter_quotes)
    ratio = grounded / total if total > 0 else 1.0
    passed = ratio >= 0.8  # Allow 20% paraphrased

    return {
        "check": "quote_grounding",
        "passed": passed,
        "value": f"{grounded}/{total}",
        "detail": (
            f"{grounded}/{total} quotes grounded ({ratio:.0%}). "
            + (f"Ungrounded: {ungrounded[:3]}" if ungrounded else "All verified.")
        ),
    }


# ---------------------------------------------------------------------------
# Check 6: Structural Quality
# ---------------------------------------------------------------------------
def check_structure(text: str) -> dict:
    """Check for good chapter structure: heading, paragraphs, scene opening."""
    issues = []

    # Check for chapter heading
    if not re.match(r'^#\s+', text.strip()):
        issues.append("Missing chapter heading (# Title)")

    # Check paragraph count
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 5:
        issues.append(f"Only {len(paragraphs)} paragraphs (expected 5+)")

    # Check for scene opening (first paragraph should be vivid, not expository)
    if paragraphs:
        first_para = paragraphs[0] if not paragraphs[0].startswith('#') else (
            paragraphs[1] if len(paragraphs) > 1 else ""
        )
        # Weak openings: starting with "In this chapter" or "This chapter" etc.
        weak_starts = [
            r'^in this chapter',
            r'^this chapter',
            r'^chapter \d',
            r'^the following',
            r'^i will now',
        ]
        for pattern in weak_starts:
            if re.match(pattern, first_para.lower()):
                issues.append("Weak scene opening (too expository)")
                break

    # Check for first-person voice
    first_person_count = len(re.findall(r'\bI\b', text))
    words = len(text.split())
    fp_ratio = first_person_count / max(words, 1)
    if fp_ratio < 0.01:
        issues.append("Very few first-person references (is this first-person narrative?)")

    passed = len(issues) == 0
    return {
        "check": "structure",
        "passed": passed,
        "value": len(issues),
        "detail": "; ".join(issues) if issues else "Good structure",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_checks(file_path: str, source_file: Optional[str] = None) -> list[dict]:
    with open(file_path) as f:
        text = f.read()

    results = []
    results.append(check_word_count(text))
    results.append(check_readability(text))
    results.append(check_timeline(text))
    results.append(check_structure(text))
    results.append(check_quote_grounding(text, source_file))

    return results


def run_multi_file_checks(files: list[str], source_file: Optional[str] = None) -> dict:
    """Run checks across multiple chapter files."""
    all_results = {}
    texts_for_consistency = []

    for fpath in sorted(files):
        fname = os.path.basename(fpath)
        with open(fpath) as f:
            text = f.read()
        texts_for_consistency.append((fname, text))
        all_results[fname] = run_checks(fpath, source_file)

    # Cross-file name consistency check
    if len(texts_for_consistency) > 1:
        name_result = check_name_consistency(texts_for_consistency)
        all_results["_cross_file"] = [name_result]
    elif len(texts_for_consistency) == 1:
        name_result = check_name_consistency(texts_for_consistency)
        all_results[os.path.basename(files[0])].append(name_result)

    return all_results


def print_results(all_results: dict, as_json: bool = False):
    if as_json:
        print(json.dumps(all_results, indent=2, default=str))
        return

    total_checks = 0
    total_passed = 0

    for fname, checks in sorted(all_results.items()):
        if fname == "_cross_file":
            print(f"\n{'=' * 60}")
            print(f"  CROSS-FILE CHECKS")
            print(f"{'=' * 60}")
        else:
            print(f"\n{'=' * 60}")
            print(f"  {fname}")
            print(f"{'=' * 60}")

        for check in checks:
            status = "PASS" if check["passed"] else "FAIL"
            icon = "  [PASS]" if check["passed"] else "  [FAIL]"
            print(f"{icon} {check['check']}: {check['detail']}")
            total_checks += 1
            if check["passed"]:
                total_passed += 1

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY: {total_passed}/{total_checks} checks passed")
    if total_passed == total_checks:
        print(f"  STATUS: ALL CLEAR")
    else:
        print(f"  STATUS: {total_checks - total_passed} issue(s) need attention")
    print(f"{'=' * 60}")

    return total_passed == total_checks


def main():
    parser = argparse.ArgumentParser(
        description="Quick quality check for autobiography chapters"
    )
    parser.add_argument(
        "path",
        help="Chapter file or directory of chapters"
    )
    parser.add_argument(
        "--source", "-s",
        help="Source transcript file for quote grounding check",
        default=None,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=3500,
        help="Minimum word count (default: 3500)",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=5000,
        help="Maximum word count (default: 5000)",
    )

    args = parser.parse_args()
    path = Path(args.path)

    if path.is_dir():
        files = sorted([str(f) for f in path.glob("*.md")])
        if not files:
            print(f"No .md files found in {path}")
            sys.exit(1)
        all_results = run_multi_file_checks(files, args.source)
    elif path.is_file():
        all_results = run_multi_file_checks([str(path)], args.source)
    else:
        print(f"Path not found: {path}")
        sys.exit(1)

    success = print_results(all_results, as_json=args.json)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
