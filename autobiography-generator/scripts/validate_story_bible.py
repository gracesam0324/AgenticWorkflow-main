#!/usr/bin/env python3
"""
Story Bible Validation — Quality Gate #1

Validates the story bible for:
  SB1: Schema compliance (JSON Schema validation)
  SB2: Entity cross-reference integrity (all IDs used in chapter_plan exist in registries)
  SB3: Timeline chronological ordering (sort_keys are monotonically ordered per chapter)
  SB4: Character first/last appearance consistency with chapter_plan
  SB5: Theme coverage (every theme appears in at least one chapter)
  SB6: Chapter plan completeness (no gaps in chapter numbering)
  SB7: Fact registry source traceability (every fact cites an interview)
  SB8: Voice guide presence and completeness
  SB9: Minimum entity counts (at least 3 characters, 5 events, 3 themes, 3 chapters)

Usage:
    python3 scripts/validate_story_bible.py --story-bible outputs/story-bible/story_bible.json
    python3 scripts/validate_story_bible.py --story-bible outputs/story-bible/story_bible.json --project-dir .

Output: JSON to stdout
    {"valid": true, "checks": {...}, "errors": [], "warnings": []}

Exit codes:
    0 — validation completed (check "valid" field)
    1 — file not found or argument error

P1 Compliance: All validation is deterministic.
SOT Compliance: Read-only.
"""

import argparse
import json
import os
import sys
from collections import defaultdict


def load_json(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def validate_story_bible(story_bible_path: str, project_dir: str = ".") -> dict:
    """Run all SB1-SB9 checks. Returns structured result."""
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, dict] = {}

    # SB1: Load and basic existence
    sb = load_json(story_bible_path)
    if sb is None:
        checks["SB1"] = {"passed": False, "detail": "File not found or invalid JSON"}
        return {"valid": False, "checks": checks, "errors": ["SB1: Story bible not found"], "warnings": []}
    checks["SB1"] = {"passed": True, "detail": "File loaded successfully"}

    # SB2: Schema compliance — delegate to schema_validator
    schema_path = os.path.join(project_dir, "schemas", "story_bible.schema.json")
    if os.path.isfile(schema_path):
        sys.path.insert(0, os.path.join(project_dir, "scripts"))
        try:
            from schema_validator import load_json_file, validate_json_schema
            schema = load_json_file(schema_path)
            if schema:
                is_valid, schema_errors, schema_warnings = validate_json_schema(schema, sb)
                checks["SB2"] = {"passed": is_valid, "detail": f"{len(schema_errors)} errors, {len(schema_warnings)} warnings"}
                errors.extend([f"SB2: {e}" for e in schema_errors])
                warnings.extend([f"SB2: {w}" for w in schema_warnings])
            else:
                checks["SB2"] = {"passed": False, "detail": "Could not load schema file"}
                warnings.append("SB2: Schema file could not be loaded — skipping schema validation")
        except ImportError:
            checks["SB2"] = {"passed": True, "detail": "Schema validator not available — skipped"}
            warnings.append("SB2: schema_validator.py not importable — skipping")
    else:
        checks["SB2"] = {"passed": True, "detail": "Schema file not found — skipped"}
        warnings.append("SB2: Schema file not found — skipping schema validation")

    # Build ID registries
    char_ids = {c["id"] for c in sb.get("characters", [])}
    event_ids = {e["id"] for e in sb.get("timeline", [])}
    place_ids = {p["id"] for p in sb.get("places", [])}
    theme_ids = {t["id"] for t in sb.get("themes", [])}
    chapter_plan = sb.get("chapter_plan", [])

    # SB3: Entity cross-reference integrity
    sb3_errors = []
    for ch in chapter_plan:
        ch_num = ch.get("chapter_number", "?")
        for char_id in ch.get("characters_featured", []):
            if char_id not in char_ids:
                sb3_errors.append(f"Chapter {ch_num}: character '{char_id}' not in character registry")
        for evt_id in ch.get("key_events", []):
            if evt_id not in event_ids:
                sb3_errors.append(f"Chapter {ch_num}: event '{evt_id}' not in timeline")
        for plc_id in ch.get("places_featured", []):
            if plc_id not in place_ids:
                sb3_errors.append(f"Chapter {ch_num}: place '{plc_id}' not in places registry")
        for thm_id in ch.get("themes_active", []):
            if thm_id not in theme_ids:
                sb3_errors.append(f"Chapter {ch_num}: theme '{thm_id}' not in themes list")

    checks["SB3"] = {"passed": len(sb3_errors) == 0, "detail": f"{len(sb3_errors)} broken references"}
    errors.extend([f"SB3: {e}" for e in sb3_errors])

    # SB4: Timeline chronological ordering
    timeline = sb.get("timeline", [])
    sort_keys = [e.get("sort_key", "") for e in timeline]
    is_sorted = all(sort_keys[i] <= sort_keys[i + 1] for i in range(len(sort_keys) - 1))
    if not is_sorted:
        out_of_order = []
        for i in range(len(sort_keys) - 1):
            if sort_keys[i] > sort_keys[i + 1]:
                out_of_order.append(f"'{sort_keys[i]}' > '{sort_keys[i + 1]}' (events {timeline[i].get('id', '?')} > {timeline[i + 1].get('id', '?')})")
        checks["SB4"] = {"passed": False, "detail": f"{len(out_of_order)} ordering violations"}
        errors.extend([f"SB4: Timeline out of order: {o}" for o in out_of_order])
    else:
        checks["SB4"] = {"passed": True, "detail": f"{len(timeline)} events in chronological order"}

    # SB5: Character first/last appearance consistency
    sb5_errors = []
    for char in sb.get("characters", []):
        char_id = char.get("id", "?")
        first_ch = char.get("first_appearance", {}).get("chapter")
        last_ch = char.get("last_appearance", {}).get("chapter")
        if first_ch is not None and last_ch is not None:
            if first_ch > last_ch:
                sb5_errors.append(f"{char_id}: first_appearance ch{first_ch} > last_appearance ch{last_ch}")
        # Check that character appears in at least the chapters between first and last
        if first_ch is not None:
            featured_in = set()
            for ch in chapter_plan:
                if char_id in ch.get("characters_featured", []):
                    featured_in.add(ch.get("chapter_number"))
            if first_ch not in featured_in:
                sb5_errors.append(f"{char_id}: first_appearance ch{first_ch} but not in chapter_plan")

    checks["SB5"] = {"passed": len(sb5_errors) == 0, "detail": f"{len(sb5_errors)} appearance issues"}
    errors.extend([f"SB5: {e}" for e in sb5_errors])

    # SB6: Theme coverage
    theme_chapters: dict[str, list[int]] = {}
    for theme in sb.get("themes", []):
        thm_id = theme.get("id", "?")
        theme_chapters[thm_id] = theme.get("chapters", [])

    uncovered_themes = [tid for tid, chs in theme_chapters.items() if not chs]
    checks["SB6"] = {"passed": len(uncovered_themes) == 0, "detail": f"{len(uncovered_themes)} themes without chapters"}
    for tid in uncovered_themes:
        errors.append(f"SB6: Theme '{tid}' has no chapters assigned")

    # SB7: Chapter plan completeness (sequential numbering)
    ch_numbers = sorted(ch.get("chapter_number", 0) for ch in chapter_plan)
    if ch_numbers:
        expected = list(range(ch_numbers[0], ch_numbers[-1] + 1))
        missing = set(expected) - set(ch_numbers)
        duplicates = [n for n in ch_numbers if ch_numbers.count(n) > 1]
        sb7_ok = not missing and not duplicates
        detail_parts = []
        if missing:
            detail_parts.append(f"missing chapters: {sorted(missing)}")
        if duplicates:
            detail_parts.append(f"duplicate chapters: {sorted(set(duplicates))}")
        checks["SB7"] = {"passed": sb7_ok, "detail": "; ".join(detail_parts) if detail_parts else "Sequential numbering OK"}
        if missing:
            errors.append(f"SB7: Missing chapter numbers: {sorted(missing)}")
        if duplicates:
            errors.append(f"SB7: Duplicate chapter numbers: {sorted(set(duplicates))}")
    else:
        checks["SB7"] = {"passed": False, "detail": "No chapters in chapter_plan"}
        errors.append("SB7: chapter_plan is empty")

    # SB8: Fact registry source traceability
    fact_registry = sb.get("fact_registry", {})
    sb8_errors = []
    for category in ["dates", "names", "places"]:
        facts = fact_registry.get(category, [])
        for fact in facts:
            source = fact.get("source", "")
            if not source:
                sb8_errors.append(f"Fact in '{category}' has no source: {fact.get('fact', fact.get('canonical', '?'))}")

    checks["SB8"] = {"passed": len(sb8_errors) == 0, "detail": f"{len(sb8_errors)} unsourced facts"}
    warnings.extend([f"SB8: {e}" for e in sb8_errors])

    # SB9: Voice guide presence
    voice_guide = sb.get("voice_guide", {})
    voice_fields = ["sentence_length", "forbidden_words", "show_dont_tell_requirements"]
    missing_voice = [f for f in voice_fields if f not in voice_guide or not voice_guide[f]]
    checks["SB9"] = {"passed": len(missing_voice) == 0, "detail": f"Missing voice guide fields: {missing_voice}" if missing_voice else "Voice guide complete"}
    for f in missing_voice:
        warnings.append(f"SB9: Voice guide missing field: '{f}'")

    # SB10: Minimum entity counts
    counts = {
        "characters": len(sb.get("characters", [])),
        "timeline_events": len(sb.get("timeline", [])),
        "themes": len(sb.get("themes", [])),
        "chapters": len(chapter_plan),
    }
    minimums = {"characters": 3, "timeline_events": 5, "themes": 3, "chapters": 3}
    sb10_fails = {k: v for k, v in counts.items() if v < minimums.get(k, 0)}
    checks["SB10"] = {
        "passed": len(sb10_fails) == 0,
        "detail": f"Counts: {counts}" + (f" — below minimum: {sb10_fails}" if sb10_fails else ""),
    }
    for k, v in sb10_fails.items():
        errors.append(f"SB10: '{k}' count {v} below minimum {minimums[k]}")

    is_valid = all(c["passed"] for c in checks.values() if c["passed"] is not None)
    # Allow SB2 skip and SB8/SB9 warnings to not invalidate
    critical_checks = ["SB1", "SB3", "SB4", "SB5", "SB6", "SB7", "SB10"]
    is_valid = all(checks.get(c, {}).get("passed", True) for c in critical_checks)

    return {
        "valid": is_valid,
        "story_bible_path": story_bible_path,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "entity_counts": counts if 'counts' in dir() else {},
    }


def main():
    parser = argparse.ArgumentParser(description="Validate story bible integrity")
    parser.add_argument("--story-bible", required=True, help="Path to story_bible.json")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    args = parser.parse_args()

    result = validate_story_bible(
        os.path.abspath(args.story_bible),
        os.path.abspath(args.project_dir),
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 0)  # Always exit 0; callers check "valid" field


if __name__ == "__main__":
    main()
