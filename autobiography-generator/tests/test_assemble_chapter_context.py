"""Tests for assemble_chapter_context.py — Chapter context assembly pipeline.

Covers: estimate_tokens, truncate_to_budget, load_json, read_text,
filter_story_bible_for_chapter, extract_interview_segments,
extract_previous_chapter_context, compute_section_budgets, assemble_context.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.assemble_chapter_context import (
    BUDGET_INTERVIEWS,
    BUDGET_PREV_CHAPTERS,
    BUDGET_STORY_BIBLE,
    CHARS_PER_TOKEN,
    assemble_context,
    compute_section_budgets,
    estimate_tokens,
    extract_interview_segments,
    extract_previous_chapter_context,
    filter_story_bible_for_chapter,
    load_json,
    read_text,
    truncate_to_budget,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────


@pytest.fixture
def sample_story_bible():
    return {
        "subject": {"name": "Park Jimin", "born": 1990},
        "meta": {
            "version": 3,
            "narrative_voice": "first-person-past",
            "tone_profile": {"warmth": 0.8},
            "golden_exemplars": ["The salt air carried memories."],
            "controlling_metaphor": {"term": "the sea", "object": "life's journey"},
        },
        "voice_guide": {
            "style": "reflective",
            "voice_fingerprint": {"sentence_length_avg": 15},
        },
        "fact_registry": {"birth_year": 1990},
        "emotional_cycle": {
            "chapter_assignments": [
                {"chapter": 1, "target_emotion": "nostalgia"},
                {"chapter": 2, "target_emotion": "tension"},
                {"chapter": 3, "target_emotion": "hope"},
            ],
        },
        "characters": [
            {"id": "char-01", "name": "Father", "importance": "primary", "relationship": "father"},
            {"id": "char-02", "name": "Mother", "importance": "primary", "relationship": "mother"},
            {"id": "char-03", "name": "Taehyung", "importance": "secondary", "relationship": "friend"},
        ],
        "timeline": [
            {"id": "evt-01", "description": "Birth", "sort_key": "1990"},
            {"id": "evt-02", "description": "Started school", "sort_key": "1996"},
            {"id": "evt-03", "description": "Moved to Seoul", "sort_key": "2002"},
            {"id": "evt-04", "description": "University entrance", "sort_key": "2008"},
        ],
        "places": [
            {"id": "place-01", "name": "Busan"},
            {"id": "place-02", "name": "Seoul"},
        ],
        "themes": [
            {"id": "theme-01", "name": "Family"},
            {"id": "theme-02", "name": "Growth"},
        ],
        "chapter_plan": [
            {
                "chapter_number": 1,
                "characters_featured": ["char-01", "char-02"],
                "key_events": ["evt-01", "evt-02"],
                "places_featured": ["place-01"],
                "themes_active": ["theme-01"],
                "source_interviews": ["INT-001"],
                "target_word_count": 5000,
                "narrative_technique": "chronological",
                "opening_hook": "The salt air...",
                "closing_bridge": "But change was coming.",
                "embellishment_cap": 0.10,
                "depth_score": 0.6,
                "metaphor_appearances": ["neutral"],
            },
            {
                "chapter_number": 2,
                "characters_featured": ["char-01", "char-03"],
                "key_events": ["evt-03"],
                "places_featured": ["place-01", "place-02"],
                "themes_active": ["theme-01", "theme-02"],
                "source_interviews": ["INT-001", "INT-002"],
                "target_word_count": 4000,
                "narrative_technique": "parallel",
            },
            {
                "chapter_number": 3,
                "characters_featured": ["char-03"],
                "key_events": ["evt-04"],
                "places_featured": ["place-02"],
                "themes_active": ["theme-02"],
                "source_interviews": ["INT-002"],
                "target_word_count": 4500,
            },
        ],
    }


@pytest.fixture
def sample_interview_transcript():
    return {
        "meta": {"session_id": "INT-001"},
        "segments": [
            {
                "segment_id": "SEG-001",
                "topic": "Childhood",
                "content": "We lived in Busan.",
                "key_quotes": [{"text": "The sea was our playground."}],
                "people_mentioned": [{"name": "Father"}],
                "emotional_markers": [{"emotion": "nostalgia", "intensity": 7}],
            },
            {
                "segment_id": "SEG-002",
                "topic": "School",
                "content": "I loved reading.",
                "key_quotes": [],
                "people_mentioned": [],
                "emotional_markers": [],
            },
        ],
    }


@pytest.fixture
def project_with_story_bible(tmp_path, sample_story_bible, sample_interview_transcript):
    sb_dir = tmp_path / "outputs" / "story-bible"
    sb_dir.mkdir(parents=True)
    with open(sb_dir / "story_bible.json", "w") as f:
        json.dump(sample_story_bible, f)

    int_dir = tmp_path / "outputs" / "interviews"
    int_dir.mkdir(parents=True)
    with open(int_dir / "INT-001.json", "w") as f:
        json.dump(sample_interview_transcript, f)

    ch_dir = tmp_path / "outputs" / "chapters"
    ch_dir.mkdir(parents=True)

    return tmp_path


# ──────────────────────────────────────────────
# estimate_tokens / truncate_to_budget
# ──────────────────────────────────────────────


class TestEstimateTokens:
    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_known_length(self):
        text = "a" * 100
        assert estimate_tokens(text) == 100 // CHARS_PER_TOKEN

    def test_proportional(self):
        assert estimate_tokens("ab" * 50) > estimate_tokens("ab" * 25)


class TestTruncateToBudget:
    def test_short_text_unchanged(self):
        text = "Hello world"
        assert truncate_to_budget(text, 1000) == text

    def test_long_text_truncated(self):
        text = "x" * 10000
        result = truncate_to_budget(text, 10)
        max_chars = 10 * CHARS_PER_TOKEN
        assert len(result) < len(text)
        assert "[... truncated to fit token budget ...]" in result

    def test_exact_boundary(self):
        budget = 5
        text = "a" * (budget * CHARS_PER_TOKEN)
        assert truncate_to_budget(text, budget) == text

    def test_one_over_boundary(self):
        budget = 5
        text = "a" * (budget * CHARS_PER_TOKEN + 1)
        result = truncate_to_budget(text, budget)
        assert "[... truncated" in result


# ──────────────────────────────────────────────
# load_json / read_text
# ──────────────────────────────────────────────


class TestLoadJson:
    def test_valid_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}')
        assert load_json(str(f)) == {"key": "value"}

    def test_nonexistent_file(self):
        assert load_json("/nonexistent/path.json") is None

    def test_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not valid json {{{")
        assert load_json(str(f)) is None

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("")
        assert load_json(str(f)) is None


class TestReadText:
    def test_valid_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        assert read_text(str(f)) == "hello world"

    def test_nonexistent_file(self):
        assert read_text("/nonexistent/path.txt") is None

    def test_unicode(self, tmp_path):
        f = tmp_path / "korean.txt"
        f.write_text("한국어 텍스트")
        assert read_text(str(f)) == "한국어 텍스트"


# ──────────────────────────────────────────────
# filter_story_bible_for_chapter
# ──────────────────────────────────────────────


class TestFilterStoryBibleForChapter:
    def test_chapter_1_returns_relevant_data(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 1)
        assert "error" not in result
        assert result["chapter_plan"]["chapter_number"] == 1
        char_ids = [c["id"] for c in result["characters"] if "id" in c]
        assert "char-01" in char_ids
        assert "char-02" in char_ids

    def test_nonexistent_chapter_returns_error(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 99)
        assert "error" in result

    def test_adjacent_chapter_characters_included(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 1)
        char_ids = [c["id"] for c in result["characters"] if "id" in c]
        # Chapter 2 is adjacent to chapter 1, so char-03 (Taehyung) should be included
        assert "char-03" in char_ids

    def test_primary_characters_always_included(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 3)
        char_names = [c["name"] for c in result["characters"]]
        # Father and Mother are primary — should be included even in ch3
        assert "Father" in char_names
        assert "Mother" in char_names

    def test_relevant_events_filtered(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 1)
        event_ids = [e["id"] for e in result["events_focused"]]
        assert "evt-01" in event_ids
        assert "evt-02" in event_ids
        assert "evt-04" not in event_ids

    def test_context_events_include_surrounding(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 1)
        context_ids = [e["id"] for e in result["events_context"]]
        # Should include surrounding events for context
        assert len(context_ids) >= len([e["id"] for e in result["events_focused"]])

    def test_places_filtered(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 1)
        place_ids = [p["id"] for p in result["places"]]
        assert "place-01" in place_ids
        assert "place-02" not in place_ids

    def test_themes_filtered(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 1)
        theme_ids = [t["id"] for t in result["themes"]]
        assert "theme-01" in theme_ids
        assert "theme-02" not in theme_ids

    def test_source_interviews_returned(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 1)
        assert "INT-001" in result["source_interviews"]

    def test_voice_guide_included(self, sample_story_bible):
        result = filter_story_bible_for_chapter(sample_story_bible, 1)
        assert result["voice_guide"]["style"] == "reflective"

    def test_empty_chapter_plan(self):
        sb = {"chapter_plan": []}
        result = filter_story_bible_for_chapter(sb, 1)
        assert "error" in result

    def test_no_chapter_plan_key(self):
        sb = {}
        result = filter_story_bible_for_chapter(sb, 1)
        assert "error" in result


# ──────────────────────────────────────────────
# extract_interview_segments
# ──────────────────────────────────────────────


class TestExtractInterviewSegments:
    def test_loads_existing_transcript(self, project_with_story_bible):
        segments = extract_interview_segments(
            str(project_with_story_bible), ["INT-001"], {}
        )
        assert len(segments) == 2
        assert segments[0]["segment_id"] == "SEG-001"

    def test_missing_transcript_returns_error(self, project_with_story_bible):
        segments = extract_interview_segments(
            str(project_with_story_bible), ["INT-999"], {}
        )
        assert len(segments) == 1
        assert "error" in segments[0]

    def test_empty_interview_list(self, project_with_story_bible):
        segments = extract_interview_segments(
            str(project_with_story_bible), [], {}
        )
        assert segments == []

    def test_budget_truncation(self, tmp_path):
        int_dir = tmp_path / "outputs" / "interviews"
        int_dir.mkdir(parents=True)
        # Create a huge interview that exceeds budget
        huge_transcript = {
            "segments": [
                {
                    "segment_id": f"SEG-{i:03d}",
                    "topic": f"Topic {i}",
                    "content": "x" * 50000,
                    "key_quotes": [],
                    "people_mentioned": [],
                    "emotional_markers": [],
                }
                for i in range(100)
            ]
        }
        with open(int_dir / "INT-001.json", "w") as f:
            json.dump(huge_transcript, f)

        segments = extract_interview_segments(str(tmp_path), ["INT-001"], {})
        # Should have truncation note
        last_seg = segments[-1]
        assert "_note" in last_seg or len(segments) < 100

    def test_multiple_interviews(self, tmp_path):
        int_dir = tmp_path / "outputs" / "interviews"
        int_dir.mkdir(parents=True)
        for iid in ["INT-001", "INT-002"]:
            with open(int_dir / f"{iid}.json", "w") as f:
                json.dump({
                    "segments": [{"segment_id": "SEG-001", "topic": "T", "content": "C"}]
                }, f)

        segments = extract_interview_segments(str(tmp_path), ["INT-001", "INT-002"], {})
        interview_ids = [s.get("interview_id") for s in segments if "interview_id" in s]
        assert "INT-001" in interview_ids
        assert "INT-002" in interview_ids


# ──────────────────────────────────────────────
# extract_previous_chapter_context
# ──────────────────────────────────────────────


class TestExtractPreviousChapterContext:
    def test_chapter_1_returns_empty(self, tmp_path):
        result = extract_previous_chapter_context(str(tmp_path), 1)
        assert result["previous_chapter_summaries"] == []
        assert result["last_chapter_closing"] == ""

    def test_chapter_2_reads_chapter_1(self, tmp_path):
        ch_dir = tmp_path / "outputs" / "chapters"
        ch_dir.mkdir(parents=True)

        # Create chapter 1 draft
        prose = "Opening paragraph.\n\nMiddle content here.\n\nClosing paragraph of chapter 1."
        (ch_dir / "ch01_draft_v1.md").write_text(prose)

        # Create chapter 1 metadata
        meta = {
            "meta": {"title": "The Beginning"},
            "structure": {"chapter_arc": "reflective -> hopeful", "closing_line": "And so it began."},
            "continuity_check": {
                "unresolved_threads": ["Father's secret"],
                "characters_referenced": ["Father", "Mother"],
            },
        }
        with open(ch_dir / "ch01_draft_v1.meta.json", "w") as f:
            json.dump(meta, f)

        result = extract_previous_chapter_context(str(tmp_path), 2)
        assert len(result["previous_chapter_summaries"]) == 1
        assert result["previous_chapter_summaries"][0]["title"] == "The Beginning"
        assert "Father's secret" in [t["thread"] for t in result["unresolved_threads"]]
        assert "Father" in result["active_characters"]

    def test_picks_latest_version(self, tmp_path):
        ch_dir = tmp_path / "outputs" / "chapters"
        ch_dir.mkdir(parents=True)

        (ch_dir / "ch01_draft_v1.md").write_text("Version 1 content.\n\nOld closing.")
        (ch_dir / "ch01_draft_v2.md").write_text("Version 2 content.\n\nNew closing.")

        result = extract_previous_chapter_context(str(tmp_path), 2)
        assert "New closing" in result["last_chapter_closing"]

    def test_no_chapters_dir(self, tmp_path):
        result = extract_previous_chapter_context(str(tmp_path), 5)
        assert result["previous_chapter_summaries"] == []

    def test_deduplicates_active_characters(self, tmp_path):
        ch_dir = tmp_path / "outputs" / "chapters"
        ch_dir.mkdir(parents=True)

        for ch in [1, 2]:
            meta = {
                "meta": {"title": f"Ch {ch}"},
                "structure": {"chapter_arc": "", "closing_line": ""},
                "continuity_check": {
                    "unresolved_threads": [],
                    "characters_referenced": ["Father", "Mother"],
                },
            }
            with open(ch_dir / f"ch{ch:02d}_draft_v1.meta.json", "w") as f:
                json.dump(meta, f)

        result = extract_previous_chapter_context(str(tmp_path), 3)
        assert len(result["active_characters"]) == len(set(result["active_characters"]))


# ──────────────────────────────────────────────
# compute_section_budgets
# ──────────────────────────────────────────────


class TestComputeSectionBudgets:
    def test_few_events_3_sections(self):
        plan = {"key_events": ["e1", "e2"]}
        budgets = compute_section_budgets(plan, 3000)
        assert len(budgets) == 3

    def test_medium_events_4_sections(self):
        plan = {"key_events": ["e1", "e2", "e3"]}
        budgets = compute_section_budgets(plan, 4000)
        assert len(budgets) == 4

    def test_many_events_5_sections(self):
        plan = {"key_events": [f"e{i}" for i in range(6)]}
        budgets = compute_section_budgets(plan, 5000)
        assert len(budgets) == 5

    def test_budgets_sum_to_target(self):
        plan = {"key_events": ["e1", "e2", "e3"]}
        budgets = compute_section_budgets(plan, 4000)
        total = sum(b["word_budget"] for b in budgets)
        assert abs(total - 4000) <= len(budgets)  # Allow rounding

    def test_section_roles_assigned(self):
        plan = {"key_events": [f"e{i}" for i in range(6)]}
        budgets = compute_section_budgets(plan, 5000)
        roles = [b["role"] for b in budgets]
        assert roles[0] == "opening"
        assert "climax" in roles

    def test_token_budget_set(self):
        plan = {"key_events": ["e1"]}
        budgets = compute_section_budgets(plan, 3000)
        for b in budgets:
            assert b["token_budget"] == b["word_budget"] * 2

    def test_empty_events(self):
        plan = {"key_events": []}
        budgets = compute_section_budgets(plan, 3000)
        assert len(budgets) == 3

    def test_no_events_key(self):
        plan = {}
        budgets = compute_section_budgets(plan, 3000)
        assert len(budgets) == 3


# ──────────────────────────────────────────────
# assemble_context (integration)
# ──────────────────────────────────────────────


class TestAssembleContext:
    def test_full_assembly(self, project_with_story_bible):
        result = assemble_context(1, str(project_with_story_bible))
        assert "error" not in result
        assert result["meta"]["chapter_number"] == 1
        assert "voice_anchors" in result
        assert "story_bible_filtered" in result
        assert "interview_segments" in result
        assert "section_budgets" in result
        assert "chapter_plan" in result
        assert "controlling_metaphor" in result
        assert "writing_instructions" in result

    def test_token_budget_summary(self, project_with_story_bible):
        result = assemble_context(1, str(project_with_story_bible))
        budget = result["meta"]["token_budget"]
        assert budget["story_bible"]["allocated"] == BUDGET_STORY_BIBLE
        assert budget["interviews"]["allocated"] == BUDGET_INTERVIEWS
        assert budget["previous_chapters"]["allocated"] == BUDGET_PREV_CHAPTERS
        assert budget["total_used"] == (
            budget["story_bible"]["used"]
            + budget["interviews"]["used"]
            + budget["previous_chapters"]["used"]
        )

    def test_missing_story_bible(self, tmp_path):
        result = assemble_context(1, str(tmp_path))
        assert "error" in result

    def test_nonexistent_chapter(self, project_with_story_bible):
        result = assemble_context(99, str(project_with_story_bible))
        assert "error" in result

    def test_voice_anchors_in_start_zone(self, project_with_story_bible):
        result = assemble_context(1, str(project_with_story_bible))
        va = result["voice_anchors"]
        assert va["golden_exemplars"] == ["The salt air carried memories."]
        assert va["voice_guide"]["style"] == "reflective"

    def test_controlling_metaphor_in_end_zone(self, project_with_story_bible):
        result = assemble_context(1, str(project_with_story_bible))
        cm = result["controlling_metaphor"]
        assert "the sea" in cm["instruction"]

    def test_emotional_target_set(self, project_with_story_bible):
        result = assemble_context(1, str(project_with_story_bible))
        assert result["emotional_target"]["target_emotion"] == "nostalgia"

    def test_writing_instructions(self, project_with_story_bible):
        result = assemble_context(1, str(project_with_story_bible))
        wi = result["writing_instructions"]
        assert wi["narrative_voice"] == "first-person-past"
        assert wi["opening_hook"] == "The salt air..."
        assert wi["embellishment_cap"] == 0.10

    def test_u_shaped_context_positioning(self, project_with_story_bible):
        result = assemble_context(1, str(project_with_story_bible))
        keys = list(result.keys())
        assert keys[0] == "voice_anchors"  # START
        assert keys[-1] == "controlling_metaphor"  # END
