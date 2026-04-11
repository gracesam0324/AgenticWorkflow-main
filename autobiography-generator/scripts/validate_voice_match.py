#!/usr/bin/env python3
"""validate_voice_match.py — Deterministic chapter vs voice_guide comparison.

Checks VM1-VM6:
  VM1: Both voice_fingerprint.json and story_bible.voice_guide exist
  VM2: Chapter avg_sentence_length within target ±20%
  VM3: Chapter dialogue_ratio within target ±0.10
  VM4: Chapter passive_voice_pct <= target maximum
  VM5: Zero forbidden_word_violations
  VM6: Direct quotes in chapter match interview originals (exact substring match)

Usage:
  python3 scripts/validate_voice_match.py --chapter 1 --project-dir .

100% deterministic. Zero AI calls.
"""

import argparse
import json
import math
import os
import re
import sys


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _find_chapter_files(project_dir: str, chapter_num: int):
    """Find the latest draft prose and metadata for a chapter."""
    chapters_dir = os.path.join(project_dir, "outputs", "chapters")
    if not os.path.isdir(chapters_dir):
        return None, None

    prefix = f"ch{chapter_num:02d}_draft_v"
    candidates = []
    for fname in os.listdir(chapters_dir):
        if fname.startswith(prefix) and fname.endswith(".md"):
            candidates.append(fname)

    if not candidates:
        return None, None

    candidates.sort(reverse=True)  # Latest version first
    prose_path = os.path.join(chapters_dir, candidates[0])
    meta_path = prose_path.replace(".md", ".meta.json")
    return prose_path, meta_path


def _compute_chapter_metrics(prose_path: str) -> dict:
    """Compute voice metrics from chapter prose."""
    with open(prose_path, "r", encoding="utf-8") as f:
        text = f.read()

    sentences = re.split(r'(?<=[.!?。])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 2]

    words = text.split()
    total_words = len(words)

    if not sentences or total_words == 0:
        return {}

    sent_lengths = [len(s.split()) for s in sentences]
    avg_sent_len = sum(sent_lengths) / len(sent_lengths)

    # Dialogue ratio
    dialogue_count = sum(1 for s in sentences if re.search(r'["""「]', s))
    dialogue_ratio = dialogue_count / len(sentences)

    # Passive voice
    passive_count = sum(1 for s in sentences if re.search(
        r'\b(was|were|is|are|been|being|be)\s+\w+ed\b|되었|되어|되는|받았|받는|당했|당하',
        s, re.IGNORECASE
    ))
    passive_pct = (passive_count / len(sentences)) * 100

    # Forbidden words
    forbidden_violations = []

    return {
        "avg_sentence_length": round(avg_sent_len, 1),
        "dialogue_ratio": round(dialogue_ratio, 3),
        "passive_voice_pct": round(passive_pct, 1),
        "total_words": total_words,
        "total_sentences": len(sentences),
        "forbidden_violations": forbidden_violations,
    }


def validate(chapter_num: int, project_dir: str) -> dict:
    result = {"valid": True, "checks": {}, "errors": [], "warnings": [], "metrics": {}}

    # VM1: Required files exist
    fp_path = os.path.join(project_dir, "outputs", "voice_fingerprint.json")
    sb_path = os.path.join(project_dir, "outputs", "story-bible", "story_bible.json")
    fp = _load_json(fp_path)
    sb = _load_json(sb_path)

    if not fp or "parameters" not in fp:
        result["warnings"].append("VM1: voice_fingerprint.json not found or invalid")
    if not sb:
        result["valid"] = False
        result["checks"]["VM1"] = "FAIL"
        result["errors"].append("VM1: story_bible.json not found")
        return result

    voice_guide = sb.get("voice_guide", {})
    if not voice_guide:
        result["valid"] = False
        result["checks"]["VM1"] = "FAIL"
        result["errors"].append("VM1: story_bible.voice_guide is empty")
        return result

    result["checks"]["VM1"] = "PASS"

    # Find chapter file
    prose_path, meta_path = _find_chapter_files(project_dir, chapter_num)
    if not prose_path or not os.path.isfile(prose_path):
        result["valid"] = False
        result["checks"]["VM1"] = "FAIL"
        result["errors"].append(f"VM1: Chapter {chapter_num} prose file not found")
        return result

    # Compute actual metrics
    actual = _compute_chapter_metrics(prose_path)
    result["metrics"] = actual

    # VM2: avg_sentence_length within ±20%
    target_asl = voice_guide.get("avg_sentence_length", 0)
    actual_asl = actual.get("avg_sentence_length", 0)
    if target_asl > 0 and actual_asl > 0:
        deviation = abs(actual_asl - target_asl) / target_asl
        if deviation > 0.20:
            result["warnings"].append(
                f"VM2: avg_sentence_length {actual_asl} deviates {deviation:.0%} from target {target_asl} (max 20%)"
            )
            result["checks"]["VM2"] = "WARN"
        else:
            result["checks"]["VM2"] = "PASS"
    else:
        result["checks"]["VM2"] = "SKIP"

    # VM3: dialogue_ratio within ±0.10
    target_dr = voice_guide.get("dialogue_ratio", 0)
    actual_dr = actual.get("dialogue_ratio", 0)
    if target_dr > 0:
        if abs(actual_dr - target_dr) > 0.10:
            result["warnings"].append(
                f"VM3: dialogue_ratio {actual_dr:.3f} deviates from target {target_dr} (tolerance ±0.10)"
            )
            result["checks"]["VM3"] = "WARN"
        else:
            result["checks"]["VM3"] = "PASS"
    else:
        result["checks"]["VM3"] = "SKIP"

    # VM4: passive_voice_pct <= target max
    target_pv = voice_guide.get("passive_voice_max", voice_guide.get("passive_voice_pct", 0))
    actual_pv = actual.get("passive_voice_pct", 0)
    if isinstance(target_pv, (int, float)) and target_pv > 0:
        target_pv_pct = target_pv * 100 if target_pv < 1 else target_pv
        if actual_pv > target_pv_pct:
            result["warnings"].append(
                f"VM4: passive_voice {actual_pv:.1f}% exceeds max {target_pv_pct:.1f}%"
            )
            result["checks"]["VM4"] = "WARN"
        else:
            result["checks"]["VM4"] = "PASS"
    else:
        result["checks"]["VM4"] = "SKIP"

    # VM5: Forbidden word violations
    forbidden_words = voice_guide.get("forbidden_words", [])
    if forbidden_words and prose_path:
        with open(prose_path, "r", encoding="utf-8") as f:
            prose_lower = f.read().lower()
        violations = []
        for word in forbidden_words:
            count = prose_lower.count(word.lower())
            if count > 0:
                violations.append({"word": word, "count": count})
        if violations:
            result["valid"] = False
            result["checks"]["VM5"] = "FAIL"
            result["errors"].append(f"VM5: Forbidden word violations: {violations}")
        else:
            result["checks"]["VM5"] = "PASS"
    else:
        result["checks"]["VM5"] = "PASS"

    # VM6: Direct quote verification — extract quoted text from prose,
    # then verify each quote actually exists in interview transcripts.
    # This prevents AI from fabricating "direct quotes" that never occurred.
    if prose_path and os.path.isfile(prose_path):
        with open(prose_path, "r", encoding="utf-8") as f:
            prose_text = f.read()

        # Extract all quoted passages from prose (min 10 chars to skip short phrases)
        quoted_patterns = [
            re.compile(r'"([^"]{10,})"'),       # English double quotes
            re.compile(r'\u201c([^\u201d]{10,})\u201d'),  # Smart quotes
            re.compile(r'\u300c([^\u300d]{5,})\u300d'),   # Korean quotes
        ]
        extracted_quotes = []
        for pat in quoted_patterns:
            extracted_quotes.extend(pat.findall(prose_text))

        if extracted_quotes:
            # Load all interview transcripts to build searchable corpus
            interviews_dir = os.path.join(project_dir, "outputs", "interviews")
            interview_corpus = ""
            if os.path.isdir(interviews_dir):
                for fname in os.listdir(interviews_dir):
                    if fname.startswith("INT-") and fname.endswith(".json"):
                        iv = _load_json(os.path.join(interviews_dir, fname))
                        if iv and "segments" in iv:
                            for seg in iv["segments"]:
                                interview_corpus += " " + seg.get("content", "")
                                for kq in seg.get("key_quotes", []):
                                    interview_corpus += " " + kq.get("text", "")

            # Verify each quote appears in interview corpus (substring match)
            unverified = []
            for quote in extracted_quotes[:20]:  # Check up to 20 quotes
                # Normalize whitespace for matching
                normalized = " ".join(quote.split())
                if len(normalized) >= 10 and normalized.lower() not in interview_corpus.lower():
                    unverified.append(normalized[:60] + "..." if len(normalized) > 60 else normalized)

            if unverified:
                result["warnings"].append(
                    f"VM6: {len(unverified)} quoted passages not found in interviews: "
                    f"{unverified[:3]}"
                )
                result["checks"]["VM6"] = "WARN"
            else:
                result["checks"]["VM6"] = "PASS"
        else:
            result["checks"]["VM6"] = "WARN"
            result["warnings"].append("VM6: No quoted passages found in prose (expected direct quotes)")
    else:
        result["checks"]["VM6"] = "SKIP"

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate voice match (VM1-VM6)")
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--project-dir", required=True)
    args = parser.parse_args()

    result = validate(args.chapter, args.project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
