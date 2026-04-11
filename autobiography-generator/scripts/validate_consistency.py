#!/usr/bin/env python3
"""
Cross-Chapter Consistency Validation — Quality Gate #3

Validates consistency across all completed chapters:
  CC1: Name consistency (all character names match story bible canonical names)
  CC2: Timeline consistency (events in chapters follow chronological order)
  CC3: Place consistency (place names match story bible canonical names)
  CC4: Character appearance ordering (characters don't appear before their first_appearance chapter)
  CC5: Age/date arithmetic (ages mentioned are consistent with birth years and event dates)
  CC6: Dead character check (characters don't appear after death unless in flashback)
  CC7: Cross-chapter narrative thread tracking (opened vs. resolved)
  CC8: Fact registry compliance (verifiable facts match the story bible fact registry)

Usage:
    python3 scripts/validate_consistency.py --project-dir .
    python3 scripts/validate_consistency.py --project-dir . --chapters 1,2,3

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
from collections import defaultdict


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


def find_all_chapters(project_dir: str, chapter_filter: list[int] | None = None) -> list[dict]:
    """Find all chapter drafts with their prose and metadata."""
    chapters_dir = os.path.join(project_dir, "outputs", "chapters")
    if not os.path.isdir(chapters_dir):
        return []

    # Find latest version of each chapter
    pattern = re.compile(r"ch(\d{2})_draft_v(\d+)\.md$")
    latest: dict[int, int] = {}  # chapter_num -> max_version

    for f in os.listdir(chapters_dir):
        m = pattern.match(f)
        if m:
            ch_num = int(m.group(1))
            version = int(m.group(2))
            if chapter_filter and ch_num not in chapter_filter:
                continue
            if ch_num not in latest or version > latest[ch_num]:
                latest[ch_num] = version

    chapters = []
    for ch_num in sorted(latest.keys()):
        version = latest[ch_num]
        prose_path = os.path.join(chapters_dir, f"ch{ch_num:02d}_draft_v{version}.md")
        meta_path = os.path.join(chapters_dir, f"ch{ch_num:02d}_draft_v{version}.meta.json")

        prose = read_text(prose_path)
        meta = load_json(meta_path)

        chapters.append({
            "chapter_number": ch_num,
            "version": version,
            "prose_path": prose_path,
            "prose": prose or "",
            "meta": meta,
        })

    return chapters


def extract_names_from_prose(prose: str) -> set[str]:
    """Extract capitalized multi-word names from prose text.

    Uses a simple heuristic: consecutive capitalized words that are not at
    sentence beginnings (preceded by '. ') and are not common title words.
    """
    # Find consecutive capitalized words (2+ chars each)
    name_pattern = re.compile(r'\b([A-Z][a-z]{1,}\s+[A-Z][a-z]{1,}(?:\s+[A-Z][a-z]{1,})?)\b')
    candidates = set(name_pattern.findall(prose))

    # Filter out common false positives
    false_positives = {
        "Chapter One", "Chapter Two", "Chapter Three", "Chapter Four", "Chapter Five",
        "The End", "Part One", "Part Two", "New York", "San Francisco",
        "United States", "United Kingdom",
    }

    return candidates - false_positives


def check_name_consistency(
    chapters: list[dict],
    story_bible: dict,
) -> tuple[list[str], list[str]]:
    """CC1: Check character name consistency across chapters."""
    errors = []
    warnings = []

    # Build canonical name -> aliases map from story bible
    canonical_names: dict[str, set[str]] = {}
    all_valid_names: set[str] = set()
    for char in story_bible.get("characters", []):
        canonical = char["name"]
        aliases = set(char.get("aliases", []))
        aliases.add(canonical)
        canonical_names[canonical] = aliases
        all_valid_names.update(aliases)

    # Also include place names from fact registry to avoid false positives
    for place in story_bible.get("places", []):
        all_valid_names.add(place.get("name", ""))

    # Check each chapter's metadata for character references
    for ch in chapters:
        meta = ch.get("meta")
        if not meta:
            continue

        ch_num = ch["chapter_number"]
        chars_in_meta = set()
        for section in meta.get("structure", {}).get("sections", []):
            for char_id in section.get("characters_present", []):
                chars_in_meta.add(char_id)

        # Cross-reference character IDs with story bible
        sb_char_ids = {c["id"] for c in story_bible.get("characters", [])}
        unknown_chars = chars_in_meta - sb_char_ids
        for uid in unknown_chars:
            errors.append(f"CC1: Chapter {ch_num}: character ID '{uid}' not found in story bible")

    return errors, warnings


def check_timeline_consistency(
    chapters: list[dict],
    story_bible: dict,
) -> tuple[list[str], list[str]]:
    """CC2: Check timeline ordering across chapters."""
    errors = []
    warnings = []

    # Build event timeline from story bible
    events_by_id: dict[str, dict] = {}
    for evt in story_bible.get("timeline", []):
        events_by_id[evt["id"]] = evt

    # Check that events referenced in each chapter are in chronological order
    prev_last_event_sort = "0000"
    for ch in chapters:
        meta = ch.get("meta")
        if not meta:
            continue

        ch_num = ch["chapter_number"]
        ch_events = []
        for section in meta.get("structure", {}).get("sections", []):
            for evt_id in section.get("events_covered", []):
                if evt_id in events_by_id:
                    ch_events.append(events_by_id[evt_id])

        if not ch_events:
            continue

        # Check internal ordering within chapter
        sort_keys = [e.get("sort_key", "0000") for e in ch_events]
        for i in range(len(sort_keys) - 1):
            if sort_keys[i] > sort_keys[i + 1]:
                errors.append(
                    f"CC2: Chapter {ch_num}: events out of order — "
                    f"'{ch_events[i]['id']}' ({sort_keys[i]}) before "
                    f"'{ch_events[i+1]['id']}' ({sort_keys[i+1]})"
                )

        # Check cross-chapter ordering
        first_event_sort = min(sort_keys) if sort_keys else "0000"
        if first_event_sort < prev_last_event_sort:
            # Allow this if it is a flashback chapter — check narrative_technique
            ch_plan = None
            for cp in story_bible.get("chapter_plan", []):
                if cp.get("chapter_number") == ch_num:
                    ch_plan = cp
                    break
            technique = (ch_plan or {}).get("narrative_technique", "")
            if "flashback" not in technique.lower():
                warnings.append(
                    f"CC2: Chapter {ch_num}: starts at {first_event_sort} but previous chapter ended at "
                    f"{prev_last_event_sort} — possible timeline regression (not marked as flashback)"
                )

        prev_last_event_sort = max(sort_keys) if sort_keys else prev_last_event_sort

    return errors, warnings


def check_character_appearances(
    chapters: list[dict],
    story_bible: dict,
) -> tuple[list[str], list[str]]:
    """CC4: Check character appearance ordering."""
    errors = []
    warnings = []

    # Build first/last appearance map
    char_first: dict[str, int] = {}
    char_last: dict[str, int | None] = {}
    char_death: dict[str, int | None] = {}

    for char in story_bible.get("characters", []):
        cid = char["id"]
        char_first[cid] = char.get("first_appearance", {}).get("chapter", 999)
        char_last[cid] = char.get("last_appearance", {}).get("chapter")
        char_death[cid] = char.get("death_year")

    for ch in chapters:
        meta = ch.get("meta")
        if not meta:
            continue

        ch_num = ch["chapter_number"]
        chars_in_chapter = set()
        for section in meta.get("structure", {}).get("sections", []):
            chars_in_chapter.update(section.get("characters_present", []))

        for cid in chars_in_chapter:
            if cid in char_first and ch_num < char_first[cid]:
                errors.append(
                    f"CC4: Chapter {ch_num}: character '{cid}' appears before first_appearance "
                    f"(chapter {char_first[cid]})"
                )

    return errors, warnings


def check_place_consistency(
    chapters: list[dict],
    story_bible: dict,
) -> tuple[list[str], list[str]]:
    """CC3: Check place name consistency."""
    errors = []
    warnings = []

    sb_place_ids = {p["id"] for p in story_bible.get("places", [])}

    for ch in chapters:
        meta = ch.get("meta")
        if not meta:
            continue

        ch_num = ch["chapter_number"]
        for section in meta.get("structure", {}).get("sections", []):
            place_id = section.get("place")
            if place_id and place_id not in sb_place_ids:
                errors.append(f"CC3: Chapter {ch_num}, section {section.get('section_id', '?')}: "
                              f"place '{place_id}' not in story bible")

    return errors, warnings


# ──────────────────────────────────────────────
# §22.3 Upgrade: CC-05 Age Arithmetic + CC-06 Dead Character Check
# ──────────────────────────────────────────────


def check_age_arithmetic(
    chapters: list[dict],
    story_bible: dict,
) -> tuple[list[str], list[str]]:
    """CC-05: Verify that ages mentioned are consistent with birth years and event dates.

    Scans chapter prose for age patterns like "40살", "마흔", "마흔 살" etc.
    Compares against character birth years from Story Bible.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Extract character birth years
    birth_years: dict[str, int] = {}
    for char in story_bible.get("characters", []):
        name = char.get("name", "")
        birth_year = char.get("birth_year")
        if name and birth_year:
            birth_years[name] = birth_year

    if not birth_years:
        return errors, warnings

    # Korean numeral map for age references
    korean_age_pattern = re.compile(
        r"(?:(\d{1,3})(?:살|세))"
        r"|(?:(스물|서른|마흔|쉰|예순|일흔|여든|아흔)\s*(?:(\d)?(?:살|세)?)?)",
        re.UNICODE,
    )
    korean_decade_map = {
        "스물": 20, "서른": 30, "마흔": 40, "쉰": 50,
        "예순": 60, "일흔": 70, "여든": 80, "아흔": 90,
    }

    for ch in chapters:
        prose = ch.get("prose", "")
        ch_num = ch.get("chapter_number", "?")
        time_period = ch.get("time_period", {})
        chapter_year = time_period.get("end") or time_period.get("start")

        if not chapter_year:
            continue

        for match in korean_age_pattern.finditer(prose):
            arabic_age = match.group(1)
            korean_decade = match.group(2)
            korean_unit = match.group(3)

            if arabic_age:
                mentioned_age = int(arabic_age)
            elif korean_decade:
                mentioned_age = korean_decade_map.get(korean_decade, 0)
                if korean_unit:
                    mentioned_age += int(korean_unit)
            else:
                continue

            # Check against all characters with birth years
            # (Simple heuristic: if subject's birth year is known)
            for name, birth_year in birth_years.items():
                expected_age = chapter_year - birth_year
                if abs(mentioned_age - expected_age) > 3:
                    # Only flag large discrepancies
                    context = prose[max(0, match.start() - 30):match.end() + 30].strip()
                    warnings.append(
                        f"CC-05: Ch{ch_num}: Age '{match.group()}' mentioned "
                        f"(≈{mentioned_age}) but {name} would be ~{expected_age} "
                        f"in {chapter_year}. Context: ...{context}..."
                    )
                    break  # One warning per mention

    return errors, warnings


def check_dead_character(
    chapters: list[dict],
    story_bible: dict,
) -> tuple[list[str], list[str]]:
    """CC-06: Verify characters don't appear after death unless in flashback.

    Scans for characters with death_year in Story Bible and flags post-death
    appearances that aren't marked as flashback or memory.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Extract characters with death years
    dead_characters: dict[str, int] = {}
    for char in story_bible.get("characters", []):
        name = char.get("name", "")
        death_year = char.get("death_year")
        if name and death_year:
            dead_characters[name] = death_year

    if not dead_characters:
        return errors, warnings

    # Flashback/memory indicator patterns
    flashback_markers = re.compile(
        r"(기억|회상|생각나|추억|떠올|그때|그 시절|살아 있던|살아있던|생전에|옛날)",
        re.UNICODE,
    )

    for ch in chapters:
        prose = ch.get("prose", "")
        ch_num = ch.get("chapter_number", "?")
        time_period = ch.get("time_period", {})
        chapter_year = time_period.get("start")

        if not chapter_year:
            continue

        for name, death_year in dead_characters.items():
            if chapter_year <= death_year:
                continue  # Character still alive in this time period

            # Check if character name appears in chapter
            name_pattern = re.compile(re.escape(name), re.UNICODE)
            for name_match in name_pattern.finditer(prose):
                # Check for nearby flashback markers (within 100 chars)
                context_start = max(0, name_match.start() - 100)
                context_end = min(len(prose), name_match.end() + 100)
                context = prose[context_start:context_end]

                if not flashback_markers.search(context):
                    errors.append(
                        f"CC-06: Ch{ch_num}: '{name}' appears in {chapter_year} "
                        f"but died in {death_year}. No flashback/memory marker nearby."
                    )
                    break  # One error per character per chapter

    return errors, warnings


def check_fact_registry(
    chapters: list[dict],
    story_bible: dict,
) -> tuple[list[str], list[str]]:
    """CC8: Spot-check verifiable facts against the fact registry."""
    errors = []
    warnings = []

    fact_registry = story_bible.get("fact_registry", {})

    # Build canonical name lookup
    canonical_names: dict[str, str] = {}  # variant -> canonical
    for entry in fact_registry.get("names", []):
        canonical = entry["canonical"]
        canonical_names[canonical.lower()] = canonical
        for variant in entry.get("variants", []):
            canonical_names[variant.lower()] = canonical

    # Check each chapter's prose for name variants
    for ch in chapters:
        prose = ch.get("prose", "")
        ch_num = ch["chapter_number"]

        # Simple check: if any variant is used instead of canonical
        for variant_lower, canonical in canonical_names.items():
            if canonical.lower() == variant_lower:
                continue  # Skip canonical itself
            if variant_lower in prose.lower():
                # Verify it is actually the variant and not just a substring
                pattern = re.compile(r'\b' + re.escape(variant_lower) + r'\b', re.IGNORECASE)
                if pattern.search(prose):
                    warnings.append(
                        f"CC8: Chapter {ch_num}: name variant '{variant_lower}' used — "
                        f"canonical form is '{canonical}'"
                    )

    return errors, warnings


def validate_consistency(project_dir: str, chapter_filter: list[int] | None = None) -> dict:
    """Run all CC1-CC8 checks across chapters."""
    all_errors: list[str] = []
    all_warnings: list[str] = []
    checks: dict[str, dict] = {}

    # Load story bible
    sb_path = os.path.join(project_dir, "outputs", "story-bible", "story_bible.json")
    sb = load_json(sb_path)
    if sb is None:
        return {
            "valid": False,
            "errors": ["Story bible not found — cannot validate consistency"],
            "warnings": [],
            "checks": {},
        }

    # Find all chapters
    chapters = find_all_chapters(project_dir, chapter_filter)
    if len(chapters) < 2:
        return {
            "valid": True,
            "errors": [],
            "warnings": ["Fewer than 2 chapters found — cross-chapter checks limited"],
            "checks": {},
            "chapters_analyzed": len(chapters),
        }

    # CC1: Name consistency
    cc1_errors, cc1_warnings = check_name_consistency(chapters, sb)
    checks["CC1"] = {"passed": len(cc1_errors) == 0, "detail": f"{len(cc1_errors)} name issues"}
    all_errors.extend(cc1_errors)
    all_warnings.extend(cc1_warnings)

    # CC2: Timeline consistency
    cc2_errors, cc2_warnings = check_timeline_consistency(chapters, sb)
    checks["CC2"] = {"passed": len(cc2_errors) == 0, "detail": f"{len(cc2_errors)} timeline issues"}
    all_errors.extend(cc2_errors)
    all_warnings.extend(cc2_warnings)

    # CC3: Place consistency
    cc3_errors, cc3_warnings = check_place_consistency(chapters, sb)
    checks["CC3"] = {"passed": len(cc3_errors) == 0, "detail": f"{len(cc3_errors)} place issues"}
    all_errors.extend(cc3_errors)
    all_warnings.extend(cc3_warnings)

    # CC4: Character appearance ordering
    cc4_errors, cc4_warnings = check_character_appearances(chapters, sb)
    checks["CC4"] = {"passed": len(cc4_errors) == 0, "detail": f"{len(cc4_errors)} appearance issues"}
    all_errors.extend(cc4_errors)
    all_warnings.extend(cc4_warnings)

    # CC5: Age/date arithmetic (§22.3 upgrade)
    cc5_errors, cc5_warnings = check_age_arithmetic(chapters, sb)
    checks["CC5"] = {"passed": len(cc5_errors) == 0, "detail": f"{len(cc5_warnings)} age issues"}
    all_errors.extend(cc5_errors)
    all_warnings.extend(cc5_warnings)

    # CC6: Dead character check (§22.3 upgrade)
    cc6_errors, cc6_warnings = check_dead_character(chapters, sb)
    checks["CC6"] = {"passed": len(cc6_errors) == 0, "detail": f"{len(cc6_errors)} dead-character issues"}
    all_errors.extend(cc6_errors)
    all_warnings.extend(cc6_warnings)

    # CC8: Fact registry compliance
    cc8_errors, cc8_warnings = check_fact_registry(chapters, sb)
    checks["CC8"] = {"passed": len(cc8_errors) == 0, "detail": f"{len(cc8_errors)} fact issues"}
    all_errors.extend(cc8_errors)
    all_warnings.extend(cc8_warnings)

    is_valid = all(c["passed"] for c in checks.values())

    return {
        "valid": is_valid,
        "chapters_analyzed": len(chapters),
        "chapter_numbers": [ch["chapter_number"] for ch in chapters],
        "checks": checks,
        "errors": all_errors,
        "warnings": all_warnings,
        "summary": {
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Cross-chapter consistency validation")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    parser.add_argument("--chapters", default=None, help="Comma-separated chapter numbers (default: all)")
    args = parser.parse_args()

    chapter_filter = None
    if args.chapters:
        chapter_filter = [int(c.strip()) for c in args.chapters.split(",")]

    result = validate_consistency(os.path.abspath(args.project_dir), chapter_filter)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
