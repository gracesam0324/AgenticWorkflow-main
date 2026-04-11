#!/usr/bin/env python3
"""validate_pacs_floor.py — Python-computed minimum pACS score (floor).

Prevents AI self-assessment inflation by computing an objective floor
based on deterministic metrics. If AI's pACS exceeds floor + 20,
a "likely inflation" warning is raised.

Floor computation:
  F_floor = (sourced_segments / total_segments) * 100
  C_floor = min(100, (word_count / target_word_count) * 100)
  L_floor = max(0, 100 - timeline_errors*10 - name_mismatches*5)
  composite_floor = min(F_floor, C_floor, L_floor)

Usage:
  python3 scripts/validate_pacs_floor.py --step 6 --project-dir .
  python3 scripts/validate_pacs_floor.py --step 9 --chapter 3 --project-dir .

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


def _count_name_mismatches(prose_path: str, sb_path: str) -> int:
    """Count character name variants that don't match story bible canonical names."""
    sb = _load_json(sb_path)
    if not sb or not os.path.isfile(prose_path):
        return 0

    characters = sb.get("characters", [])
    canonical_names = set()
    known_aliases = set()
    for char in characters:
        name = char.get("name", "")
        if name:
            canonical_names.add(name)
        for alias in char.get("aliases", []):
            known_aliases.add(alias)

    with open(prose_path, "r", encoding="utf-8") as f:
        prose = f.read()

    # Simple heuristic: look for capitalized words that resemble names
    # but aren't in canonical or alias sets
    # This is a basic check — not perfect but deterministic
    mismatches = 0
    all_known = canonical_names | known_aliases
    # Look for names near possessive markers or dialogue attribution
    name_patterns = re.findall(r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:said|told|asked|replied)', prose)
    for name in name_patterns:
        if name not in all_known and name not in {"The", "This", "That", "When", "After", "Before"}:
            mismatches += 1

    return mismatches


def compute_floor(step: int, project_dir: str, chapter_num: int | None = None) -> dict:
    result = {"step": step, "chapter": chapter_num, "floor": {}, "warnings": []}

    sb_path = os.path.join(project_dir, "outputs", "story-bible", "story_bible.json")
    sb = _load_json(sb_path)

    if step == 9 and chapter_num:
        # Chapter-specific floor
        ch_dir = os.path.join(project_dir, "outputs", "chapters")
        prefix = f"ch{chapter_num:02d}_draft_v"
        candidates = sorted([
            f for f in os.listdir(ch_dir)
            if f.startswith(prefix) and f.endswith(".meta.json")
        ], reverse=True) if os.path.isdir(ch_dir) else []

        if not candidates:
            result["warnings"].append(f"No metadata found for chapter {chapter_num}")
            return result

        meta = _load_json(os.path.join(ch_dir, candidates[0]))
        prose_path = os.path.join(ch_dir, candidates[0].replace(".meta.json", ".md"))

        if not meta:
            result["warnings"].append("Cannot load chapter metadata")
            return result

        trace = meta.get("source_traceability", {})

        # F_floor: source coverage
        interviews_used = len(trace.get("interviews_used", []))
        segments_ref = len(trace.get("segments_referenced", []))
        total_sections = len(meta.get("structure", {}).get("sections", []))
        if total_sections > 0:
            f_floor = min(100, (segments_ref / max(total_sections, 1)) * 100)
        else:
            f_floor = 50 if interviews_used > 0 else 0

        # C_floor: word count coverage
        actual_wc = meta.get("meta", {}).get("word_count", 0)
        target_wc = meta.get("meta", {}).get("target_word_count", 5000)
        c_floor = min(100, (actual_wc / max(target_wc, 1)) * 100) if target_wc > 0 else 50

        # L_floor: name consistency
        name_mismatches = _count_name_mismatches(prose_path, sb_path) if os.path.isfile(prose_path) else 0
        l_floor = max(0, 100 - name_mismatches * 5)

    elif step in (5, 6):
        # Story bible floor
        if not sb:
            result["warnings"].append("Story bible not found")
            return result

        chars = len(sb.get("characters", []))
        events = len(sb.get("timeline", []))
        themes = len(sb.get("themes", []))
        chapters = len(sb.get("chapter_plan", []))

        # F_floor: entity completeness
        f_floor = min(100, (chars + events + themes) * 5)

        # C_floor: chapter coverage
        c_floor = min(100, chapters * 10)

        # L_floor: structural integrity (basic)
        l_floor = 80  # Default for story bible — timeline checks done elsewhere

    else:
        result["warnings"].append(f"No floor computation defined for step {step}")
        return result

    composite = min(f_floor, c_floor, l_floor)

    result["floor"] = {
        "F_floor": round(f_floor, 1),
        "C_floor": round(c_floor, 1),
        "L_floor": round(l_floor, 1),
        "composite_floor": round(composite, 1),
    }

    # Check against AI-reported pACS if available
    pacs_log_dir = os.path.join(project_dir, "pacs-logs")
    step_key = f"step-{step}"
    if chapter_num:
        pacs_file = os.path.join(pacs_log_dir, f"step-{step}-ch{chapter_num:02d}-pacs.md")
    else:
        pacs_file = os.path.join(pacs_log_dir, f"step-{step}-pacs.md")

    if os.path.isfile(pacs_file):
        with open(pacs_file, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'pACS\s*=\s*(?:min\([^)]+\)\s*=\s*)?(\d{1,3})', content)
        if match:
            ai_pacs = int(match.group(1))
            if ai_pacs > composite + 20:
                result["warnings"].append(
                    f"INFLATION WARNING: AI pACS={ai_pacs} exceeds floor+20={composite+20:.0f}. "
                    f"Floor breakdown: F={f_floor:.0f}, C={c_floor:.0f}, L={l_floor:.0f}"
                )

    return result


def main():
    parser = argparse.ArgumentParser(description="Compute pACS floor")
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--chapter", type=int, default=None)
    parser.add_argument("--project-dir", required=True)
    args = parser.parse_args()

    result = compute_floor(args.step, args.project_dir, args.chapter)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
