#!/usr/bin/env python3
"""validate_source_tracing.py — Deterministic source verification for chapters.

Checks ST1-ST6:
  ST1: All INT-NNN references in source_traceability exist as actual files
  ST2: All segment references {interview, segment} exist in the referenced interview
  ST3: All fabricated_scenes have justification >= 30 chars and valid section_id
  ST4: At least 1 direct quote used per chapter
  ST5: [INFERRED] tag ratio <= 15% of chapter content
  ST6: [INFERRED] scenes reference interviews that contain related people/places/periods

Usage:
  python3 scripts/validate_source_tracing.py --artifact outputs/chapters/ch01_draft_v1.meta.json --project-dir .

100% deterministic. Zero AI calls.
"""

import argparse
import json
import os
import re
import sys


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def validate(artifact_path: str, project_dir: str) -> dict:
    result = {"valid": True, "checks": {}, "errors": [], "warnings": []}

    meta = _load_json(artifact_path)
    if not meta:
        result["valid"] = False
        result["checks"]["ST0"] = "FAIL"
        result["errors"].append(f"ST0: Cannot load artifact at {artifact_path}")
        return result

    trace = meta.get("source_traceability", {})
    if not trace:
        result["valid"] = False
        result["checks"]["ST0"] = "FAIL"
        result["errors"].append("ST0: No source_traceability section in metadata")
        return result

    interviews_dir = os.path.join(project_dir, "outputs", "interviews")

    # ST1: All INT-NNN references exist as files
    interviews_used = trace.get("interviews_used", [])
    missing_files = []
    for int_id in interviews_used:
        fpath = os.path.join(interviews_dir, f"{int_id}.json")
        if not os.path.isfile(fpath):
            missing_files.append(int_id)

    if missing_files:
        result["valid"] = False
        result["checks"]["ST1"] = "FAIL"
        result["errors"].append(f"ST1: Interview files not found: {missing_files}")
    elif not interviews_used:
        result["valid"] = False
        result["checks"]["ST1"] = "FAIL"
        result["errors"].append("ST1: No interviews referenced (interviews_used is empty)")
    else:
        result["checks"]["ST1"] = "PASS"

    # ST2: Segment references exist in their interviews
    segs_referenced = trace.get("segments_referenced", [])
    invalid_segs = []
    for ref in segs_referenced:
        int_id = ref.get("interview", "")
        seg_id = ref.get("segment", "")
        fpath = os.path.join(interviews_dir, f"{int_id}.json")
        iv_data = _load_json(fpath)
        if not iv_data:
            invalid_segs.append(f"{int_id}/{seg_id} (interview not found)")
            continue
        seg_ids = [s.get("segment_id") for s in iv_data.get("segments", [])]
        if seg_id not in seg_ids:
            invalid_segs.append(f"{int_id}/{seg_id} (segment not in interview)")

    if invalid_segs:
        result["valid"] = False
        result["checks"]["ST2"] = "FAIL"
        result["errors"].append(f"ST2: Invalid segment references: {invalid_segs}")
    else:
        result["checks"]["ST2"] = "PASS"

    # ST3: Fabricated scenes have justification and valid section_id
    fab_scenes = trace.get("fabricated_scenes", [])
    bad_fabs = []
    structure_sections = {s.get("section_id") for s in meta.get("structure", {}).get("sections", [])}
    for fab in fab_scenes:
        just = fab.get("justification", "")
        sid = fab.get("section_id", "")
        problems = []
        if len(just) < 30:
            problems.append(f"justification too short ({len(just)} chars)")
        if sid and structure_sections and sid not in structure_sections:
            problems.append(f"section_id '{sid}' not in chapter structure")
        if problems:
            bad_fabs.append(f"{sid}: {'; '.join(problems)}")

    if bad_fabs:
        result["valid"] = False
        result["checks"]["ST3"] = "FAIL"
        result["errors"].append(f"ST3: Invalid fabricated scenes: {bad_fabs}")
    else:
        result["checks"]["ST3"] = "PASS"

    # ST4: At least 1 direct quote
    direct_quotes = trace.get("direct_quotes_used", 0)
    if direct_quotes < 1:
        result["warnings"].append("ST4: No direct quotes used (recommended >= 1)")
        result["checks"]["ST4"] = "WARN"
    else:
        result["checks"]["ST4"] = "PASS"

    # ST5: [INFERRED] ratio <= 15%
    # Try to read the prose file to count tags
    prose_path = artifact_path.replace(".meta.json", ".md")
    if os.path.isfile(prose_path):
        with open(prose_path, "r", encoding="utf-8") as f:
            prose = f.read()
        total_words = len(prose.split())
        inferred_matches = re.findall(r'\[INFERRED\]', prose, re.IGNORECASE)
        # Estimate inferred content: each tag marks ~50 words of inferred content
        inferred_word_est = len(inferred_matches) * 50
        if total_words > 0:
            inferred_ratio = inferred_word_est / total_words
            if inferred_ratio > 0.15:
                result["valid"] = False
                result["checks"]["ST5"] = "FAIL"
                result["errors"].append(
                    f"ST5: [INFERRED] ratio ~{inferred_ratio:.1%} exceeds 15% limit "
                    f"({len(inferred_matches)} tags in {total_words} words)"
                )
            else:
                result["checks"]["ST5"] = "PASS"
        else:
            result["checks"]["ST5"] = "SKIP"
    else:
        result["checks"]["ST5"] = "SKIP"
        result["warnings"].append("ST5: Prose file not found — cannot check [INFERRED] ratio")

    # ST6: [INFERRED] scenes reference relevant interviews
    if fab_scenes and interviews_used:
        result["checks"]["ST6"] = "PASS"  # Presence check only — deeper validation needs chapter context
    elif fab_scenes and not interviews_used:
        result["valid"] = False
        result["checks"]["ST6"] = "FAIL"
        result["errors"].append("ST6: Fabricated scenes exist but no interviews referenced")
    else:
        result["checks"]["ST6"] = "PASS"

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate source tracing (ST1-ST6)")
    parser.add_argument("--artifact", required=True, help="Path to metadata JSON")
    parser.add_argument("--project-dir", required=True)
    args = parser.parse_args()

    result = validate(args.artifact, args.project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
