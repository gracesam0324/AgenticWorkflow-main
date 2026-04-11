#!/usr/bin/env python3
"""
Chapter Context Assembly — Pre-processing for @chapter-writer

Assembles a focused context package for writing a specific chapter by:
1. Reading the story bible and filtering to relevant characters/places/events
2. Reading relevant interview transcripts and extracting pertinent segments
3. Extracting previous chapter summaries for continuity
4. Computing token budget per section
5. Producing a single context injection file

Usage:
    python3 scripts/assemble_chapter_context.py --chapter 3 --project-dir .

Output: outputs/chapters/ch{NN}_context.json

Architecture:
    RLM Pattern: Context package is an external memory object (file on disk).
    P1 Compliance: Deterministic extraction — no AI inference.
    P2 Compliance: Prepares focused context so the writer agent operates efficiently.

Token Budget Philosophy:
    Claude's effective context ≈ 185K tokens (200K - system overhead).
    Reserve 40K for story bible + voice guide.
    Reserve 30K for interview segments.
    Reserve 15K for previous chapter context.
    Reserve 100K for the agent's reasoning + output generation.
"""

import argparse
import json
import os
import sys
from typing import Any


# Token estimation: mixed content ≈ 4 chars/token (English prose)
CHARS_PER_TOKEN = 4

# Budget allocation (in tokens) — Quality-first: maximize context richness
# Absolute Criterion 1: quality > token cost. Model = Opus 4.6 (1M context).
# Design: provide FULL context to maximize cross-reference, voice consistency,
# and narrative continuity. Truncation is a last resort, not a default.
BUDGET_STORY_BIBLE = 80_000      # Full story bible — untruncated character/place/theme/timeline
BUDGET_INTERVIEWS = 120_000      # All interview transcripts — cross-reference anecdotes
BUDGET_PREV_CHAPTERS = 80_000    # 3+ full previous chapters — voice/tone continuity
BUDGET_BLUEPRINT = 10_000        # Full blueprint — structural constraints, kickpoints
BUDGET_STYLE = 15_000            # Full style guide + exemplars + blended voice metadata
BUDGET_TOTAL = (BUDGET_STORY_BIBLE + BUDGET_INTERVIEWS + BUDGET_PREV_CHAPTERS
                + BUDGET_BLUEPRINT + BUDGET_STYLE)
# Total: ~305K tokens — well within 1M context. Leaves 695K for reasoning + output.


def estimate_tokens(text: str) -> int:
    """Estimate token count from character count."""
    return len(text) // CHARS_PER_TOKEN


def truncate_to_budget(text: str, budget_tokens: int) -> str:
    """Truncate text to fit within token budget."""
    max_chars = budget_tokens * CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... truncated to fit token budget ...]"


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


def filter_story_bible_for_chapter(sb: dict, chapter_num: int) -> dict:
    """Extract story bible data relevant to a specific chapter."""

    # Find the chapter plan entry
    chapter_plan_entry = None
    for cp in sb.get("chapter_plan", []):
        if cp.get("chapter_number") == chapter_num:
            chapter_plan_entry = cp
            break

    if not chapter_plan_entry:
        return {"error": f"No chapter plan entry found for chapter {chapter_num}"}

    # Extract relevant IDs
    relevant_char_ids = set(chapter_plan_entry.get("characters_featured", []))
    relevant_event_ids = set(chapter_plan_entry.get("key_events", []))
    relevant_place_ids = set(chapter_plan_entry.get("places_featured", []))
    relevant_theme_ids = set(chapter_plan_entry.get("themes_active", []))
    source_interviews = set(chapter_plan_entry.get("source_interviews", []))

    # Also include characters from adjacent chapters for continuity awareness
    all_plans = sb.get("chapter_plan", [])
    for cp in all_plans:
        if abs(cp.get("chapter_number", 0) - chapter_num) == 1:
            relevant_char_ids.update(cp.get("characters_featured", []))

    # Filter characters — include full data for relevant ones, summary for others
    relevant_characters = []
    for char in sb.get("characters", []):
        if char["id"] in relevant_char_ids:
            relevant_characters.append(char)
        elif char.get("importance") == "primary":
            # Include minimal info for primary characters not in this chapter
            relevant_characters.append({
                "id": char["id"],
                "name": char["name"],
                "relationship": char.get("relationship", ""),
                "importance": "primary",
                "_note": "Not featured in this chapter — included for reference only",
            })

    # Filter timeline
    relevant_events = [e for e in sb.get("timeline", []) if e["id"] in relevant_event_ids]
    # Also include events from immediately before and after for context
    all_events = sorted(sb.get("timeline", []), key=lambda e: e.get("sort_key", ""))
    chapter_event_indices = [i for i, e in enumerate(all_events) if e["id"] in relevant_event_ids]
    if chapter_event_indices:
        min_idx = max(0, min(chapter_event_indices) - 2)
        max_idx = min(len(all_events), max(chapter_event_indices) + 3)
        context_events = all_events[min_idx:max_idx]
    else:
        context_events = relevant_events

    # Filter places
    relevant_places = [p for p in sb.get("places", []) if p["id"] in relevant_place_ids]

    # Filter themes
    relevant_themes = [t for t in sb.get("themes", []) if t["id"] in relevant_theme_ids]

    return {
        "chapter_plan": chapter_plan_entry,
        "characters": relevant_characters,
        "events_focused": relevant_events,
        "events_context": context_events,
        "places": relevant_places,
        "themes": relevant_themes,
        "source_interviews": list(source_interviews),
        "subject": sb.get("subject", {}),
        "voice_guide": sb.get("voice_guide", {}),
        "fact_registry": sb.get("fact_registry", {}),
    }


def extract_interview_segments(
    project_dir: str,
    interview_ids: list[str],
    chapter_plan: dict,
) -> list[dict]:
    """Load and filter interview transcripts to relevant segments."""
    interviews_dir = os.path.join(project_dir, "outputs", "interviews")
    segments = []
    total_chars = 0
    max_chars = BUDGET_INTERVIEWS * CHARS_PER_TOKEN

    for int_id in interview_ids:
        # Try multiple file naming conventions
        candidates = [
            os.path.join(interviews_dir, f"{int_id}.json"),
            os.path.join(interviews_dir, f"{int_id.lower()}.json"),
        ]

        transcript = None
        for path in candidates:
            transcript = load_json(path)
            if transcript:
                break

        if not transcript:
            segments.append({
                "interview_id": int_id,
                "error": "Transcript file not found",
            })
            continue

        # Extract all segments from this interview
        for seg in transcript.get("segments", []):
            segment_data = {
                "interview_id": int_id,
                "segment_id": seg.get("segment_id"),
                "topic": seg.get("topic"),
                "content": seg.get("content", ""),
                "key_quotes": seg.get("key_quotes", []),
                "people_mentioned": seg.get("people_mentioned", []),
                "emotional_markers": seg.get("emotional_markers", []),
            }

            segment_chars = len(json.dumps(segment_data))
            if total_chars + segment_chars > max_chars:
                segments.append({
                    "_note": f"Token budget reached — {len(interview_ids) - interview_ids.index(int_id)} "
                             f"interviews remaining were truncated",
                })
                return segments

            total_chars += segment_chars
            segments.append(segment_data)

    return segments


def extract_previous_chapter_context(
    project_dir: str,
    chapter_num: int,
) -> dict:
    """Extract context from previous chapters for continuity."""
    chapters_dir = os.path.join(project_dir, "outputs", "chapters")
    result = {
        "previous_chapter_summaries": [],
        "last_chapter_closing": "",
        "unresolved_threads": [],
        "active_characters": [],
    }

    if chapter_num <= 1:
        return result

    # Get the immediately previous chapter's closing paragraphs
    import re
    prev_num = chapter_num - 1
    pattern = re.compile(rf"ch{prev_num:02d}_draft_v(\d+)\.md$")
    max_version = 0

    if os.path.isdir(chapters_dir):
        for f in os.listdir(chapters_dir):
            m = pattern.match(f)
            if m:
                max_version = max(max_version, int(m.group(1)))

    if max_version > 0:
        prev_prose_path = os.path.join(chapters_dir, f"ch{prev_num:02d}_draft_v{max_version}.md")
        prev_prose = read_text(prev_prose_path)
        if prev_prose:
            # Extract last 3 paragraphs
            paragraphs = [p.strip() for p in prev_prose.split("\n\n") if p.strip() and not p.strip().startswith("#")]
            result["last_chapter_closing"] = "\n\n".join(paragraphs[-3:]) if paragraphs else ""

    # Get metadata from all previous chapters
    for prev_ch in range(max(1, chapter_num - 3), chapter_num):
        meta_pattern = re.compile(rf"ch{prev_ch:02d}_draft_v(\d+)\.meta\.json$")
        max_v = 0
        if os.path.isdir(chapters_dir):
            for f in os.listdir(chapters_dir):
                m = meta_pattern.match(f)
                if m:
                    max_v = max(max_v, int(m.group(1)))

        if max_v > 0:
            meta_path = os.path.join(chapters_dir, f"ch{prev_ch:02d}_draft_v{max_v}.meta.json")
            meta = load_json(meta_path)
            if meta:
                summary = {
                    "chapter": prev_ch,
                    "title": meta.get("meta", {}).get("title", ""),
                    "arc": meta.get("structure", {}).get("chapter_arc", ""),
                    "closing_line": meta.get("structure", {}).get("closing_line", ""),
                }
                result["previous_chapter_summaries"].append(summary)

                # Collect unresolved threads
                unresolved = meta.get("continuity_check", {}).get("unresolved_threads", [])
                result["unresolved_threads"].extend(
                    [{"from_chapter": prev_ch, "thread": t} for t in unresolved]
                )

                # Collect active characters
                result["active_characters"].extend(
                    meta.get("continuity_check", {}).get("characters_referenced", [])
                )

    # Deduplicate active characters
    result["active_characters"] = list(set(result["active_characters"]))

    # Truncate to budget
    context_str = json.dumps(result)
    if estimate_tokens(context_str) > BUDGET_PREV_CHAPTERS:
        result["last_chapter_closing"] = truncate_to_budget(
            result["last_chapter_closing"],
            BUDGET_PREV_CHAPTERS // 2,
        )

    return result


def compute_section_budgets(chapter_plan: dict, total_word_target: int) -> list[dict]:
    """Compute word count budget per planned section."""
    # Rough distribution based on narrative technique
    technique = chapter_plan.get("narrative_technique", "chronological")

    sections = []
    # Default: even distribution with heavier weight on opening and climax
    # A typical chapter has opening (15%), body (60%), climax (15%), resolution (10%)
    default_weights = [0.15, 0.30, 0.30, 0.15, 0.10]

    # Adjust weights by number of key events
    event_count = len(chapter_plan.get("key_events", []))
    if event_count <= 2:
        section_count = 3
        weights = [0.20, 0.50, 0.30]
    elif event_count <= 5:
        section_count = 4
        weights = [0.15, 0.35, 0.30, 0.20]
    else:
        section_count = 5
        weights = default_weights

    for i in range(section_count):
        word_budget = int(total_word_target * weights[i])
        sections.append({
            "section_index": i + 1,
            "role": ["opening", "rising_action", "climax", "falling_action", "resolution"][min(i, 4)],
            "word_budget": word_budget,
            "token_budget": word_budget * 2,  # Roughly 2 tokens per word for generation
        })

    return sections


def assemble_context(chapter_num: int, project_dir: str) -> dict:
    """Assemble the complete context package for a chapter."""

    # Load story bible
    sb_path = os.path.join(project_dir, "outputs", "story-bible", "story_bible.json")
    sb = load_json(sb_path)
    if sb is None:
        return {"error": "Story bible not found — cannot assemble context"}

    # Filter story bible
    filtered_sb = filter_story_bible_for_chapter(sb, chapter_num)
    if "error" in filtered_sb:
        return filtered_sb

    chapter_plan = filtered_sb["chapter_plan"]

    # Extract interview segments
    interview_ids = filtered_sb.get("source_interviews", [])
    interview_segments = extract_interview_segments(project_dir, interview_ids, chapter_plan)

    # Extract previous chapter context
    prev_context = extract_previous_chapter_context(project_dir, chapter_num)

    # Compute section budgets
    target_wc = chapter_plan.get("target_word_count", 5000)
    section_budgets = compute_section_budgets(chapter_plan, target_wc)

    # Compute token budget summary
    sb_tokens = estimate_tokens(json.dumps(filtered_sb))
    int_tokens = estimate_tokens(json.dumps(interview_segments))
    prev_tokens = estimate_tokens(json.dumps(prev_context))

    # ── Load NEW data structures (v3.1 upgrade) ──────────────────
    # Blueprint, style selection, and voice fingerprint are loaded
    # as INDEPENDENT top-level sources (not nested in story bible).

    # Load story blueprint (user's narrative intent — binding constraint)
    # CRITICAL: Do NOT silently fallback to {} — blueprint is a binding constraint.
    bp_path = os.path.join(project_dir, "outputs", "story-blueprint", "story_blueprint.json")
    blueprint = load_json(bp_path)
    if not blueprint:
        return {"error": f"CRITICAL: story_blueprint.json not found at {bp_path}. Run Step 4 (/review-blueprint) first."}

    # Load style selection metadata (selected style + blending ratio)
    # CRITICAL: Style selection drives voice_guide — cannot be empty.
    style_path = os.path.join(project_dir, "outputs", "style-selection", "style_selection.json")
    style_selection = load_json(style_path)
    if not style_selection:
        return {"error": f"CRITICAL: style_selection.json not found at {style_path}. Run Step 8 (/select-style) first."}

    # Load voice fingerprint (Python-computed, NOT AI-estimated)
    # CRITICAL: Must be from compute_voice_fingerprint.py (check source marker).
    vfp_path = os.path.join(project_dir, "outputs", "voice_fingerprint.json")
    voice_fingerprint_standalone = load_json(vfp_path)
    if not voice_fingerprint_standalone:
        return {"error": f"CRITICAL: voice_fingerprint.json not found at {vfp_path}. Run compute_voice_fingerprint.py first."}
    if voice_fingerprint_standalone.get("source") != "compute_voice_fingerprint.py":
        return {"error": f"CRITICAL: voice_fingerprint.json was NOT produced by compute_voice_fingerprint.py. Source: {voice_fingerprint_standalone.get('source', 'unknown')}"}

    # ── U-Shaped Context Positioning ──────────────────────────────
    # Critical info at START and END of context window for maximum
    # attention. Less critical info in MIDDLE. This exploits the
    # well-documented primacy/recency bias in transformer attention.
    #
    # START (highest attention): Voice anchors + Style + Blueprint constraints
    # MIDDLE (lower attention):  Interviews + Previous chapters + Events
    # END (high attention):      Chapter plan + Writing instructions + Metaphor

    # Extract golden exemplars from story bible (quality-critical anchors)
    golden_exemplars = sb.get("meta", {}).get("golden_exemplars", [])
    if not golden_exemplars:
        golden_exemplars = sb.get("golden_exemplars", [])

    # Extract controlling metaphor from story bible
    controlling_metaphor = sb.get("meta", {}).get("controlling_metaphor", {})
    if not controlling_metaphor:
        controlling_metaphor = sb.get("controlling_metaphor", {})

    # Extract voice fingerprint — prefer standalone file, fallback to nested
    voice_fingerprint = voice_fingerprint_standalone.get("parameters", {})
    if not voice_fingerprint:
        voice_fingerprint = filtered_sb.get("voice_guide", {}).get("voice_fingerprint", {})

    # Extract emotional balance target for this chapter
    emotional_cycle = sb.get("emotional_cycle", {})
    chapter_emotion = {}
    for assignment in emotional_cycle.get("chapter_assignments", []):
        if assignment.get("chapter") == chapter_num:
            chapter_emotion = assignment
            break

    # Extract embellishment cap for this chapter
    embellishment_cap = chapter_plan.get("embellishment_cap", 0.15)
    depth_score = chapter_plan.get("depth_score", 0.5)

    context_package = {
        # ═══ START ZONE (Highest Attention) ═══════════════════════
        # Voice anchors, style selection, and blueprint constraints
        # are placed FIRST so the chapter-writer's attention is
        # primed with voice targets + user intent BEFORE data.

        "voice_anchors": {
            "_position": "START — Read these FIRST to calibrate voice",
            "golden_exemplars": golden_exemplars,
            "voice_guide": filtered_sb.get("voice_guide", {}),
            "voice_fingerprint": voice_fingerprint,
        },
        "style_context": {
            "_position": "START — Writing style parameters (from Step 8)",
            "selected_style": style_selection.get("selected_style", "none"),
            "blending_ratio": style_selection.get("blending_ratio", 0.3),
            "calibration_version": style_selection.get("calibration_version", ""),
            "blend_metadata": filtered_sb.get("voice_guide", {}).get("_blend_metadata", {}),
        },
        "blueprint_constraints": {
            "_position": "START — User's narrative intent (BINDING — do not override)",
            "core_message": blueprint.get("core_message", ""),
            "structure_type": blueprint.get("structure_type", ""),
            "kickpoints": blueprint.get("kickpoints", []),
            "emphasis_areas": blueprint.get("emphasis_areas", []),
            "exclusion_areas": blueprint.get("exclusion_areas", []),
        },

        "meta": {
            "chapter_number": chapter_num,
            "generated_by": "assemble_chapter_context.py",
            "context_positioning": "U-shaped (START=voice+exemplars, MIDDLE=data, END=instructions+metaphor)",
            "story_bible_version": sb.get("meta", {}).get("version", 0),
            "token_budget": {
                "story_bible": {"allocated": BUDGET_STORY_BIBLE, "used": sb_tokens},
                "interviews": {"allocated": BUDGET_INTERVIEWS, "used": int_tokens},
                "previous_chapters": {"allocated": BUDGET_PREV_CHAPTERS, "used": prev_tokens},
                "total_used": sb_tokens + int_tokens + prev_tokens,
                "total_budget": BUDGET_TOTAL,
                "remaining_for_generation": 185_000 - (sb_tokens + int_tokens + prev_tokens),
            },
        },

        # ═══ MIDDLE ZONE (Supporting Data) ════════════════════════
        # Interview segments, characters, events, previous context.
        # These provide factual grounding but are less attention-critical
        # than voice calibration or writing instructions.

        "story_bible_filtered": {
            "subject": filtered_sb["subject"],
            "characters": filtered_sb["characters"],
            "events_focused": filtered_sb["events_focused"],
            "events_context": filtered_sb["events_context"],
            "places": filtered_sb["places"],
            "themes": filtered_sb["themes"],
            "fact_registry": filtered_sb["fact_registry"],
        },
        "interview_segments": interview_segments,
        "previous_chapter_context": prev_context,
        "section_budgets": section_budgets,

        # ═══ END ZONE (High Attention) ════════════════════════════
        # Chapter plan and writing instructions are placed LAST so they
        # are fresh in the model's attention during generation.
        # Controlling metaphor threading instructions ensure the
        # metaphor appears with intentional progression.

        "chapter_plan": chapter_plan,
        "emotional_target": chapter_emotion,
        "writing_instructions": {
            "narrative_voice": sb.get("meta", {}).get("narrative_voice", "first-person-past"),
            "tone_profile": sb.get("meta", {}).get("tone_profile", {}),
            "opening_hook": chapter_plan.get("opening_hook", ""),
            "closing_bridge": chapter_plan.get("closing_bridge", ""),
            "narrative_technique": chapter_plan.get("narrative_technique", "chronological"),
            "unresolved_threads_from_previous": prev_context.get("unresolved_threads", []),
            "embellishment_cap": embellishment_cap,
            "depth_score": depth_score,
        },
        "controlling_metaphor": {
            "_position": "END — Metaphor threading instruction (must appear in this chapter if assigned)",
            "metaphor": controlling_metaphor,
            "chapter_appearances": chapter_plan.get("metaphor_appearances", []),
            "instruction": (
                f"If this chapter is assigned a metaphor appearance, weave "
                f"'{controlling_metaphor.get('term', '')}' ({controlling_metaphor.get('object', '')}) "
                f"into the prose with the designated role (neutral/emotional/transformed). "
                f"The metaphor must feel organic, never forced."
            ) if controlling_metaphor else "No controlling metaphor assigned for this chapter.",
        },
    }

    return context_package


def main():
    parser = argparse.ArgumentParser(description="Assemble chapter writing context")
    parser.add_argument("--chapter", type=int, required=True, help="Chapter number")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    context = assemble_context(args.chapter, project_dir)

    # Write to output file
    output_dir = os.path.join(project_dir, "outputs", "chapters")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"ch{args.chapter:02d}_context.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)

    # Also print summary to stdout
    summary = {
        "chapter": args.chapter,
        "output_path": output_path,
        "token_budget": context.get("meta", {}).get("token_budget", {}),
        "characters_included": len(context.get("story_bible_filtered", {}).get("characters", [])),
        "events_included": len(context.get("story_bible_filtered", {}).get("events_focused", [])),
        "interview_segments": len(context.get("interview_segments", [])),
        "section_count": len(context.get("section_budgets", [])),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
