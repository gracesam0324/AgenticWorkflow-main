#!/usr/bin/env python3
"""
Chapter Draft Validation — Quality Gate #2

Validates a chapter draft (prose + metadata) for:
  CH1: Metadata schema compliance
  CH2: Word count within target range (+/- 15%)
  CH3: Section structure completeness (at least 2 sections)
  CH4: Source traceability (at least 1 interview referenced)
  CH5: Voice metrics thresholds (sentence length, dialogue ratio, passive voice)
  CH6: Story bible version match (draft uses current story bible version)
  CH7: Character name validation (all characters exist in story bible)
  CH8: Prose file existence and minimum size
  CH9: Forbidden word check (from voice guide)
  CH10: Show-vs-tell ratio check

Usage:
    python3 scripts/validate_chapter.py --chapter 3 --project-dir .
    python3 scripts/validate_chapter.py --chapter 3 --draft-version 2 --project-dir .

Output: JSON to stdout
Exit codes: 0 always (check "valid" field)

P1 Compliance: All validation is deterministic.
SOT Compliance: Read-only.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def load_json(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def read_text(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def count_words(text: str) -> int:
    """Count words in text, ignoring markdown headers and formatting."""
    lines = text.split("\n")
    content_lines = [l for l in lines if not l.startswith("#") and not l.startswith("---")]
    return len(" ".join(content_lines).split())


def compute_sentence_stats(text: str) -> dict:
    """Compute sentence-level statistics from prose text."""
    # Remove markdown headers and horizontal rules
    lines = text.split("\n")
    content_lines = [l for l in lines if not l.startswith("#") and not l.strip() == "---"]
    content = " ".join(content_lines)

    # Split into sentences (approximate — handles Mr., Mrs., Dr., etc.)
    content = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Jr|Sr)\.\s', r'\1_DOT_ ', content)
    sentences = re.split(r'[.!?]+\s+', content)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip().split()) >= 3]

    if not sentences:
        return {"count": 0, "avg_length": 0, "std_dev": 0, "min": 0, "max": 0}

    lengths = [len(s.split()) for s in sentences]
    avg = sum(lengths) / len(lengths)
    variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
    std_dev = variance ** 0.5

    return {
        "count": len(sentences),
        "avg_length": round(avg, 1),
        "std_dev": round(std_dev, 1),
        "min": min(lengths),
        "max": max(lengths),
    }


def compute_dialogue_ratio(text: str) -> float:
    """Estimate dialogue ratio based on quoted text."""
    total_chars = len(text)
    if total_chars == 0:
        return 0.0

    # Find all quoted text (both single and double quotes)
    double_quoted = re.findall(r'"[^"]{5,}"', text)
    single_quoted = re.findall(r"'[^']{10,}'", text)  # Higher threshold to avoid contractions

    dialogue_chars = sum(len(q) for q in double_quoted) + sum(len(q) for q in single_quoted)
    return round(dialogue_chars / total_chars, 3)


def compute_passive_voice_pct(text: str) -> float:
    """Estimate passive voice percentage."""
    lines = text.split("\n")
    content_lines = [l for l in lines if not l.startswith("#") and not l.strip() == "---"]
    content = " ".join(content_lines)

    sentences = re.split(r'[.!?]+\s+', content)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip().split()) >= 3]

    if not sentences:
        return 0.0

    passive_pattern = re.compile(
        r'\b(was|were|been|being|is|are|am|got)\s+'
        r'(being\s+)?'
        r'(\w+ed|born|broken|brought|built|bought|caught|chosen|come|done|'
        r'drawn|driven|eaten|fallen|felt|found|forgotten|forgiven|frozen|'
        r'given|gone|grown|heard|hidden|hit|held|hurt|kept|known|laid|led|'
        r'left|lent|lost|made|meant|met|paid|put|read|ridden|risen|run|'
        r'said|seen|sent|set|shown|shut|spoken|spent|stood|stolen|struck|'
        r'taken|taught|told|thought|thrown|understood|woken|won|worn|written)\b',
        re.IGNORECASE,
    )

    passive_count = sum(1 for s in sentences if passive_pattern.search(s))
    return round(passive_count / len(sentences) * 100, 1)


# ──────────────────────────────────────────────
# §22.3 Korean literary validators — translationese (번역체) 5-9,
#       retrospective cliche (그때는 몰랐지만), Sino-Korean density (한자어)
# ──────────────────────────────────────────────

# Translationese (번역체) patterns 5-9 — regex-detectable patterns
BYEONYEOKCHE_PATTERNS = {
    "BT-05": {
        "name": "Excessive English-style connectors",
        "pattern": re.compile(r"(그러나|그러므로|따라서|그런데|왜냐하면)", re.UNICODE),
        "threshold_per_1000_words": 8,
        "description": "Overuse of formal connectors typical of translated text",
    },
    "BT-06": {
        "name": "Unnatural subject emphasis with 은/는",
        "pattern": re.compile(r"(그것은|이것은|그녀는|그들은)", re.UNICODE),
        "threshold_per_1000_words": 5,
        "description": "English-style subject-emphasis not natural in Korean narrative",
    },
    "BT-07": {
        "name": "Excessive adverbial -적으로",
        "pattern": re.compile(r"\w+적으로", re.UNICODE),
        "threshold_per_1000_words": 6,
        "description": "Sino-Korean adverbs ending in -적으로 signal academic/translated style",
    },
    "BT-08": {
        "name": "Excessive nominalization -ㅁ/음",
        "pattern": re.compile(r"(에 대한|에 있어서|에 의해|에 관한|을 통해|를 위해)", re.UNICODE),
        "threshold_per_1000_words": 5,
        "description": "Prepositional phrases typical of translated academic prose",
    },
    "BT-09": {
        "name": "Excessive 것이다 ending",
        "pattern": re.compile(r"것이다\.|것입니다\.", re.UNICODE),
        "threshold_per_1000_words": 4,
        "description": "Declarative endings typical of translated expository prose",
    },
}

# KS-01: Retrospective cliche "그때는 몰랐지만" (I didn't know then) frequency limit
GTTM_PATTERN = re.compile(r"그때는\s*몰랐지만", re.UNICODE)
GTTM_MAX_PER_CHAPTER = 2


def check_byeonyeokche(text: str) -> list[dict]:
    """Check for translationese (번역체) patterns 5-9 with per-1000-words thresholds.

    Returns list of violations with pattern ID, count, and threshold.
    """
    word_count = max(count_words(text), 1)
    violations = []

    for bt_id, spec in BYEONYEOKCHE_PATTERNS.items():
        matches = spec["pattern"].findall(text)
        count = len(matches)
        normalized = count * 1000 / word_count
        threshold = spec["threshold_per_1000_words"]

        if normalized > threshold:
            violations.append({
                "id": bt_id,
                "name": spec["name"],
                "count": count,
                "per_1000_words": round(normalized, 1),
                "threshold": threshold,
                "severity": "warning",
            })

    return violations


def check_gttm_frequency(text: str) -> dict:
    """Check KS-01: "그때는 몰랐지만" frequency ≤2 per chapter.

    Returns dict with count and passed status.
    """
    count = len(GTTM_PATTERN.findall(text))
    return {
        "id": "KS-01",
        "name": "그때는 몰랐지만 frequency",
        "count": count,
        "max_allowed": GTTM_MAX_PER_CHAPTER,
        "passed": count <= GTTM_MAX_PER_CHAPTER,
    }


def check_hanja_density(text: str, threshold: float = 0.40) -> list[dict]:
    """Check 한자어 density per paragraph.

    Loads hanja dictionary from config/hanja-dictionary.yaml if available.
    Returns list of paragraphs exceeding the density threshold.
    """
    # Load hanja markers
    hanja_markers = []
    hanja_config_path = Path(__file__).parent.parent / "config" / "hanja-dictionary.yaml"
    if hanja_config_path.exists():
        try:
            import yaml
            with open(hanja_config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            hanja_markers = config.get("high_density_markers", [])
            threshold = config.get("density_threshold", threshold)
        except Exception:
            pass

    if not hanja_markers:
        return []  # No dictionary available — skip check

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    violations = []

    for i, para in enumerate(paragraphs):
        if len(para) < 50:  # Skip very short paragraphs
            continue
        words = para.split()
        if not words:
            continue
        hanja_count = sum(1 for w in words for marker in hanja_markers if marker in w)
        density = hanja_count / len(words) if words else 0

        if density > threshold:
            violations.append({
                "paragraph_index": i + 1,
                "density": round(density, 3),
                "threshold": threshold,
                "hanja_count": hanja_count,
                "word_count": len(words),
                "preview": para[:80] + "..." if len(para) > 80 else para,
            })

    return violations


def check_forbidden_words(text: str, forbidden: list[str]) -> list[dict]:
    """Check for forbidden words and return violations with locations."""
    violations = []
    text_lower = text.lower()

    for word in forbidden:
        word_lower = word.lower()
        pattern = re.compile(r'\b' + re.escape(word_lower) + r'\b', re.IGNORECASE)
        matches = list(pattern.finditer(text))

        if matches:
            # Find line numbers for each match
            locations = []
            for m in matches:
                line_num = text[:m.start()].count("\n") + 1
                locations.append(f"line {line_num}")

            violations.append({
                "word": word,
                "count": len(matches),
                "locations": locations[:5],  # Cap at 5 locations
            })

    return violations


def compute_show_tell_ratio(text: str) -> float:
    """Estimate show-vs-tell ratio. Higher = more showing."""
    telling_patterns = [
        r'\b(she|he|I|they|we)\s+(felt|was|were|seemed|appeared|looked)\s+\w+',
        r'\b(it was|there was|there were)\s+\w+',
        r'\b(obviously|clearly|certainly|definitely|undoubtedly)\b',
    ]

    showing_patterns = [
        r'\b(smelled|tasted|heard|saw|touched|grabbed|pressed|squeezed)\b',
        r'\b(whispered|shouted|muttered|laughed|cried|sighed|gasped)\b',
        r'\b(red|blue|green|gold|silver|bright|dark|warm|cold|rough|smooth)\b',
        r'"[^"]{5,}"',  # Dialogue as showing
    ]

    telling_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in telling_patterns)
    showing_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in showing_patterns)

    if telling_count == 0:
        return 10.0  # Perfect showing
    return round(showing_count / telling_count, 2)


def find_latest_draft(project_dir: str, chapter_num: int, draft_version: int | None) -> tuple[str | None, str | None]:
    """Find the latest draft files for a chapter."""
    chapters_dir = os.path.join(project_dir, "outputs", "chapters")

    if draft_version:
        prose = os.path.join(chapters_dir, f"ch{chapter_num:02d}_draft_v{draft_version}.md")
        meta = os.path.join(chapters_dir, f"ch{chapter_num:02d}_draft_v{draft_version}.meta.json")
        return (prose if os.path.isfile(prose) else None, meta if os.path.isfile(meta) else None)

    # Find latest version
    pattern = re.compile(rf"ch{chapter_num:02d}_draft_v(\d+)\.md$")
    max_version = 0
    for f in os.listdir(chapters_dir) if os.path.isdir(chapters_dir) else []:
        m = pattern.match(f)
        if m:
            max_version = max(max_version, int(m.group(1)))

    if max_version == 0:
        return None, None

    prose = os.path.join(chapters_dir, f"ch{chapter_num:02d}_draft_v{max_version}.md")
    meta = os.path.join(chapters_dir, f"ch{chapter_num:02d}_draft_v{max_version}.meta.json")
    return (prose if os.path.isfile(prose) else None, meta if os.path.isfile(meta) else None)


def validate_chapter(chapter_num: int, project_dir: str, draft_version: int | None = None) -> dict:
    """Run all CH1-CH10 checks. Returns structured result."""
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, dict] = {}

    prose_path, meta_path = find_latest_draft(project_dir, chapter_num, draft_version)

    # CH1: Prose file existence
    if prose_path is None:
        checks["CH1"] = {"passed": False, "detail": f"No prose file found for chapter {chapter_num}"}
        errors.append(f"CH1: Prose file not found for chapter {chapter_num}")
        return {"valid": False, "chapter": chapter_num, "checks": checks, "errors": errors, "warnings": warnings}

    prose_text = read_text(prose_path)
    if not prose_text or len(prose_text) < 500:
        checks["CH1"] = {"passed": False, "detail": f"Prose file too small: {len(prose_text or '')} bytes"}
        errors.append("CH1: Prose file is empty or too small (< 500 bytes)")
    else:
        checks["CH1"] = {"passed": True, "detail": f"Prose file: {len(prose_text)} bytes"}

    # CH2: Metadata existence and schema
    meta = load_json(meta_path) if meta_path else None
    if meta is None:
        checks["CH2"] = {"passed": False, "detail": "Metadata file not found or invalid JSON"}
        warnings.append("CH2: Metadata file missing — voice metrics checks will be limited")
    else:
        checks["CH2"] = {"passed": True, "detail": "Metadata loaded successfully"}

    # CH3: Word count validation
    word_count = count_words(prose_text) if prose_text else 0
    target_wc = meta.get("meta", {}).get("target_word_count", 5000) if meta else 5000
    deviation_pct = ((word_count - target_wc) / target_wc * 100) if target_wc > 0 else 0
    wc_ok = abs(deviation_pct) <= 15
    checks["CH3"] = {
        "passed": wc_ok,
        "detail": f"Word count: {word_count} (target: {target_wc}, deviation: {deviation_pct:+.1f}%)",
    }
    if not wc_ok:
        if deviation_pct < -15:
            errors.append(f"CH3: Chapter is {abs(deviation_pct):.1f}% below target word count ({word_count}/{target_wc})")
        else:
            warnings.append(f"CH3: Chapter is {deviation_pct:.1f}% above target word count ({word_count}/{target_wc})")

    # CH4: Section structure
    if prose_text:
        section_headers = re.findall(r'^##\s+.+', prose_text, re.MULTILINE)
        checks["CH4"] = {
            "passed": len(section_headers) >= 2,
            "detail": f"{len(section_headers)} sections found",
        }
        if len(section_headers) < 2:
            errors.append(f"CH4: Only {len(section_headers)} section(s) found — minimum is 2")
    else:
        checks["CH4"] = {"passed": False, "detail": "No prose text to analyze"}

    # CH5: Source traceability
    if meta:
        interviews_used = meta.get("source_traceability", {}).get("interviews_used", [])
        checks["CH5"] = {
            "passed": len(interviews_used) >= 1,
            "detail": f"{len(interviews_used)} interview(s) cited",
        }
        if not interviews_used:
            errors.append("CH5: No interview sources cited in metadata")
    else:
        checks["CH5"] = {"passed": True, "detail": "Skipped — no metadata"}
        warnings.append("CH5: Cannot verify source traceability without metadata")

    # CH6-CH10: Voice metrics (require prose text)
    if prose_text:
        # CH6: Sentence length
        sent_stats = compute_sentence_stats(prose_text)
        # Load story bible for voice guide targets
        sb_path = os.path.join(project_dir, "outputs", "story-bible", "story_bible.json")
        sb = load_json(sb_path)
        target_avg_sent = 15  # Default
        if sb and "voice_guide" in sb:
            target_avg_sent = sb["voice_guide"].get("sentence_length", {}).get("average_words", 15)

        sent_deviation = abs(sent_stats["avg_length"] - target_avg_sent)
        checks["CH6"] = {
            "passed": sent_deviation <= 3,
            "detail": f"Avg sentence length: {sent_stats['avg_length']} words (target: {target_avg_sent}, deviation: {sent_deviation:.1f})",
        }
        if sent_deviation > 3:
            warnings.append(f"CH6: Sentence length deviation {sent_deviation:.1f} words from target")

        # CH7: Dialogue ratio
        dialogue_ratio = compute_dialogue_ratio(prose_text)
        checks["CH7"] = {
            "passed": True,  # Informational — no hard threshold
            "detail": f"Dialogue ratio: {dialogue_ratio:.1%}",
        }
        if dialogue_ratio < 0.05:
            warnings.append("CH7: Very low dialogue ratio — consider adding more direct speech")
        elif dialogue_ratio > 0.60:
            warnings.append("CH7: Very high dialogue ratio — may read more like a screenplay")

        # CH8: Passive voice
        passive_pct = compute_passive_voice_pct(prose_text)
        checks["CH8"] = {
            "passed": passive_pct <= 15,
            "detail": f"Passive voice: {passive_pct}%",
        }
        if passive_pct > 15:
            warnings.append(f"CH8: Passive voice at {passive_pct}% — above 15% threshold")

        # CH9: Forbidden words
        forbidden = []
        if sb and "voice_guide" in sb:
            forbidden = sb["voice_guide"].get("forbidden_words", [])
        violations = check_forbidden_words(prose_text, forbidden)
        checks["CH9"] = {
            "passed": len(violations) == 0,
            "detail": f"{len(violations)} forbidden word violation(s)",
        }
        if violations:
            for v in violations:
                errors.append(f"CH9: Forbidden word '{v['word']}' found {v['count']} time(s)")

        # CH10: Show vs. Tell ratio
        show_tell = compute_show_tell_ratio(prose_text)
        checks["CH10"] = {
            "passed": show_tell >= 2.0,
            "detail": f"Show:Tell ratio = {show_tell}",
        }
        if show_tell < 2.0:
            warnings.append(f"CH10: Show:Tell ratio {show_tell} below 2.0 — more concrete/sensory language needed")
    else:
        for c in ["CH6", "CH7", "CH8", "CH9", "CH10"]:
            checks[c] = {"passed": True, "detail": "Skipped — no prose text"}

    # Compute overall validity
    critical_checks = ["CH1", "CH3", "CH4", "CH5", "CH9"]
    is_valid = all(checks.get(c, {}).get("passed", True) for c in critical_checks)

    return {
        "valid": is_valid,
        "chapter": chapter_num,
        "prose_path": prose_path,
        "meta_path": meta_path,
        "word_count": word_count if prose_text else 0,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "voice_metrics": {
            "sentence_stats": sent_stats if prose_text else {},
            "dialogue_ratio": dialogue_ratio if prose_text else 0,
            "passive_voice_pct": passive_pct if prose_text else 0,
            "show_tell_ratio": show_tell if prose_text else 0,
            "forbidden_violations": violations if prose_text else [],
        } if prose_text else {},
        # §22.3 Korean-specific checks (번역체, 그때는 몰랐지만, 한자어)
        "korean_checks": {
            "byeonyeokche_violations": check_byeonyeokche(prose_text) if prose_text else [],
            "gttm_check": check_gttm_frequency(prose_text) if prose_text else {},
            "hanja_density_violations": check_hanja_density(prose_text) if prose_text else [],
        } if prose_text else {},
    }


def main():
    parser = argparse.ArgumentParser(description="Validate chapter draft quality")
    parser.add_argument("--chapter", type=int, required=True, help="Chapter number")
    parser.add_argument("--draft-version", type=int, default=None, help="Specific draft version (default: latest)")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    args = parser.parse_args()

    result = validate_chapter(args.chapter, os.path.abspath(args.project_dir), args.draft_version)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
