#!/usr/bin/env python3
"""validate_interview_coverage.py — Deterministic interview completeness check.

Checks IC1-IC5:
  IC1: Total sessions >= min_sessions (default 3)
  IC2: Life period coverage — each emphasis_area has >= 1 interview segment
  IC3: Total segments >= total_chapters * 3 (minimum source density)
  IC4: Total key_quotes >= total_chapters * 2
  IC5: Emotional diversity — at least 4 of 7 emotional tones represented

Usage:
  python3 scripts/validate_interview_coverage.py --project-dir .

100% deterministic. Zero AI calls.
"""

import argparse
import json
import os
import sys


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _load_interviews(project_dir: str) -> list[dict]:
    interviews_dir = os.path.join(project_dir, "outputs", "interviews")
    if not os.path.isdir(interviews_dir):
        return []
    results = []
    for fname in sorted(os.listdir(interviews_dir)):
        if not fname.startswith("INT-") or not fname.endswith(".json"):
            continue
        data = _load_json(os.path.join(interviews_dir, fname))
        if data:
            results.append(data)
    return results


def validate(project_dir: str, min_sessions: int = 3) -> dict:
    result = {"valid": True, "checks": {}, "errors": [], "warnings": [], "stats": {}}

    interviews = _load_interviews(project_dir)

    # IC1: Session count
    session_count = len(interviews)
    result["stats"]["total_sessions"] = session_count
    if session_count < min_sessions:
        result["valid"] = False
        result["checks"]["IC1"] = "FAIL"
        result["errors"].append(f"IC1: {session_count} sessions < minimum {min_sessions}")
    else:
        result["checks"]["IC1"] = "PASS"

    # Count segments, quotes, emotions across all interviews
    total_segments = 0
    total_quotes = 0
    emotional_tones = set()
    themes_covered = set()

    for iv in interviews:
        meta = iv.get("meta", {})
        tone = meta.get("emotional_tone")
        if tone:
            emotional_tones.add(tone)
        for theme in meta.get("themes", []):
            themes_covered.add(theme)

        segments = iv.get("segments", [])
        total_segments += len(segments)
        for seg in segments:
            total_quotes += len(seg.get("key_quotes", []))

    result["stats"]["total_segments"] = total_segments
    result["stats"]["total_key_quotes"] = total_quotes
    result["stats"]["emotional_tones"] = sorted(emotional_tones)
    result["stats"]["themes_covered"] = sorted(themes_covered)

    # IC2: Theme/emphasis coverage — check if blueprint emphasis_areas are covered
    bp_path = os.path.join(project_dir, "outputs", "story-blueprint", "story_blueprint.json")
    bp = _load_json(bp_path)
    if bp:
        emphasis = bp.get("emphasis_areas", [])
        uncovered = [e for e in emphasis if not any(
            e.lower() in t.lower() for t in themes_covered
        )]
        if uncovered:
            result["warnings"].append(f"IC2: Emphasis areas not in interview themes: {uncovered}")
            result["checks"]["IC2"] = "WARN"
        else:
            result["checks"]["IC2"] = "PASS"
    else:
        result["checks"]["IC2"] = "SKIP"
        result["warnings"].append("IC2: No blueprint found — skipping emphasis coverage check")

    # IC3: Segment density
    # Load target chapters from state or blueprint
    target_chapters = 12  # default
    if bp:
        ch_outline = bp.get("chapter_outline", [])
        if ch_outline:
            target_chapters = len(ch_outline)

    required_segments = target_chapters * 3
    if total_segments < required_segments:
        result["valid"] = False
        result["checks"]["IC3"] = "FAIL"
        result["errors"].append(
            f"IC3: {total_segments} segments < required {required_segments} "
            f"({target_chapters} chapters × 3)"
        )
    else:
        result["checks"]["IC3"] = "PASS"

    # IC4: Quote density
    required_quotes = target_chapters * 2
    if total_quotes < required_quotes:
        result["warnings"].append(
            f"IC4: {total_quotes} key_quotes < recommended {required_quotes} "
            f"({target_chapters} chapters × 2)"
        )
        result["checks"]["IC4"] = "WARN"
    else:
        result["checks"]["IC4"] = "PASS"

    # IC5: Emotional diversity (at least 4 of 7 standard tones)
    standard_tones = {"reflective", "joyful", "melancholic", "neutral", "intense", "humorous", "bittersweet"}
    matched_tones = emotional_tones & standard_tones
    if len(matched_tones) < 4:
        result["warnings"].append(
            f"IC5: Only {len(matched_tones)} emotional tones represented "
            f"(found: {sorted(matched_tones)}, need >= 4)"
        )
        result["checks"]["IC5"] = "WARN"
    else:
        result["checks"]["IC5"] = "PASS"

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate interview coverage (IC1-IC5)")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--min-sessions", type=int, default=3)
    args = parser.parse_args()

    result = validate(args.project_dir, args.min_sessions)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
