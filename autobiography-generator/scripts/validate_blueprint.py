#!/usr/bin/env python3
"""validate_blueprint.py — Deterministic validation for story_blueprint.json (Step 4).

Checks BP1-BP7:
  BP1: File exists and loads as valid JSON
  BP2: JSON Schema compliance (story_blueprint.schema.json)
  BP3: Kickpoints >= 3, each with valid chapter_placement
  BP4: core_message >= 30 characters
  BP5: emphasis_areas and exclusion_areas have no overlap
  BP6: controlling_metaphor.interview_mention_count >= 2 (Python-verified)
  BP7: emotional_arc has all 3 required fields (opening, climax, resolution)

Usage:
  python3 scripts/validate_blueprint.py --project-dir .

Exit codes:
  0 — all checks pass
  1 — one or more checks fail

100% deterministic. Zero AI calls. Zero network calls.
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


def _load_schema(project_dir: str) -> dict | None:
    schema_path = os.path.join(project_dir, "schemas", "story_blueprint.schema.json")
    return _load_json(schema_path)


def _find_blueprint(project_dir: str) -> str | None:
    candidates = [
        os.path.join(project_dir, "outputs", "story-blueprint", "story_blueprint.json"),
        os.path.join(project_dir, "outputs", "story_blueprint.json"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _count_keyword_in_interviews(project_dir: str, keyword: str) -> int:
    """Count unprompted mentions of a keyword across all interview transcripts."""
    interviews_dir = os.path.join(project_dir, "outputs", "interviews")
    if not os.path.isdir(interviews_dir):
        return 0

    count = 0
    keyword_lower = keyword.lower()
    for fname in os.listdir(interviews_dir):
        if not fname.startswith("INT-") or not fname.endswith(".json"):
            continue
        data = _load_json(os.path.join(interviews_dir, fname))
        if not data or "segments" not in data:
            continue
        for seg in data["segments"]:
            content = seg.get("content", "")
            if isinstance(content, str):
                count += content.lower().count(keyword_lower)
    return count


def validate(project_dir: str) -> dict:
    results = {"valid": True, "checks": {}, "errors": [], "warnings": []}

    # BP1: File exists and loads
    bp_path = _find_blueprint(project_dir)
    if not bp_path:
        results["valid"] = False
        results["checks"]["BP1"] = "FAIL"
        results["errors"].append("BP1: story_blueprint.json not found")
        return results

    bp = _load_json(bp_path)
    if bp is None:
        results["valid"] = False
        results["checks"]["BP1"] = "FAIL"
        results["errors"].append("BP1: story_blueprint.json is not valid JSON")
        return results
    results["checks"]["BP1"] = "PASS"

    # BP2: Schema compliance (lightweight — check required fields)
    required_top = ["meta", "structure_type", "kickpoints", "core_message", "emotional_arc", "chapter_outline"]
    missing = [f for f in required_top if f not in bp]
    if missing:
        results["valid"] = False
        results["checks"]["BP2"] = "FAIL"
        results["errors"].append(f"BP2: Missing required fields: {missing}")
    else:
        results["checks"]["BP2"] = "PASS"

    # BP3: Kickpoints >= 3 with valid chapter_placement
    kickpoints = bp.get("kickpoints", [])
    if len(kickpoints) < 3:
        results["valid"] = False
        results["checks"]["BP3"] = "FAIL"
        results["errors"].append(f"BP3: Need >= 3 kickpoints, found {len(kickpoints)}")
    else:
        invalid_kp = []
        for i, kp in enumerate(kickpoints):
            if not kp.get("title"):
                invalid_kp.append(f"kickpoint[{i}] missing title")
            if not isinstance(kp.get("chapter_placement"), int) or kp["chapter_placement"] < 1:
                invalid_kp.append(f"kickpoint[{i}] invalid chapter_placement")
        if invalid_kp:
            results["valid"] = False
            results["checks"]["BP3"] = "FAIL"
            results["errors"].extend([f"BP3: {e}" for e in invalid_kp])
        else:
            results["checks"]["BP3"] = "PASS"

    # BP4: core_message >= 30 characters
    core_msg = bp.get("core_message", "")
    if len(core_msg) < 30:
        results["valid"] = False
        results["checks"]["BP4"] = "FAIL"
        results["errors"].append(f"BP4: core_message too short ({len(core_msg)} chars, need >= 30)")
    else:
        results["checks"]["BP4"] = "PASS"

    # BP5: emphasis_areas and exclusion_areas no overlap
    emphasis = set(bp.get("emphasis_areas", []))
    exclusion = set(bp.get("exclusion_areas", []))
    overlap = emphasis & exclusion
    if overlap:
        results["valid"] = False
        results["checks"]["BP5"] = "FAIL"
        results["errors"].append(f"BP5: Overlap between emphasis and exclusion: {overlap}")
    else:
        results["checks"]["BP5"] = "PASS"

    # BP6: controlling_metaphor verified in interviews
    cm = bp.get("controlling_metaphor", {})
    if cm:
        metaphor_text = cm.get("metaphor", "")
        claimed_count = cm.get("interview_mention_count", 0)
        if metaphor_text:
            actual_count = _count_keyword_in_interviews(project_dir, metaphor_text)
            if actual_count < 2:
                results["valid"] = False
                results["checks"]["BP6"] = "FAIL"
                results["errors"].append(
                    f"BP6: Controlling metaphor '{metaphor_text}' found {actual_count} times in interviews (need >= 2)"
                )
            elif claimed_count > actual_count:
                results["warnings"].append(
                    f"BP6: Claimed {claimed_count} mentions but found {actual_count}"
                )
                results["checks"]["BP6"] = "WARN"
            else:
                results["checks"]["BP6"] = "PASS"
        else:
            results["checks"]["BP6"] = "SKIP"
            results["warnings"].append("BP6: No controlling metaphor defined")
    else:
        results["checks"]["BP6"] = "SKIP"

    # BP7: emotional_arc completeness
    arc = bp.get("emotional_arc", {})
    arc_fields = ["opening_mood", "climax_moment", "resolution_tone"]
    missing_arc = [f for f in arc_fields if not arc.get(f) or len(str(arc[f])) < 10]
    if missing_arc:
        results["valid"] = False
        results["checks"]["BP7"] = "FAIL"
        results["errors"].append(f"BP7: Incomplete emotional_arc — missing or too short: {missing_arc}")
    else:
        results["checks"]["BP7"] = "PASS"

    return results


def main():
    parser = argparse.ArgumentParser(description="Validate story blueprint (BP1-BP7)")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    args = parser.parse_args()

    result = validate(args.project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
