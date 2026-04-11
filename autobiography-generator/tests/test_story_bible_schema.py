"""Tests for StoryBibleEntry schema validation.

Covers:
- Valid story bible construction
- Character name uniqueness
- Event-character cross-reference integrity
- Timeline ordering
- Individual entry validation (character, location, event)
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.schemas import (
    CharacterEntry,
    EventEntry,
    EventSignificance,
    LocationEntry,
    StoryBibleEntry,
)


# ──────────────────────────────────────────────
# CharacterEntry Tests
# ──────────────────────────────────────────────


class TestCharacterEntry:
    """Tests for individual character entries."""

    @pytest.mark.unit
    @pytest.mark.schema
    def test_valid_character(self, valid_character_data: dict[str, Any]) -> None:
        char = CharacterEntry.model_validate(valid_character_data)
        assert char.name == "Kim Minjun"
        assert "MJ" in char.aliases
        assert char.relationship == "mentor"

    @pytest.mark.unit
    @pytest.mark.schema
    def test_character_name_stripped(self) -> None:
        char = CharacterEntry.model_validate({
            "name": "  Kim Minjun  ",
            "relationship": "mentor",
        })
        assert char.name == "Kim Minjun"

    @pytest.mark.unit
    @pytest.mark.schema
    def test_character_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least 1 character"):
            CharacterEntry.model_validate({
                "name": "   ",
                "relationship": "mentor",
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_character_missing_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CharacterEntry.model_validate({"relationship": "mentor"})

    @pytest.mark.unit
    @pytest.mark.schema
    def test_character_missing_relationship_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CharacterEntry.model_validate({"name": "Kim Minjun"})

    @pytest.mark.unit
    @pytest.mark.schema
    def test_character_invalid_session_format(self) -> None:
        with pytest.raises(ValidationError, match="String should match pattern"):
            CharacterEntry.model_validate({
                "name": "Kim Minjun",
                "relationship": "mentor",
                "first_appearance_session": "SESSION-1",
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_character_valid_session_format(self) -> None:
        char = CharacterEntry.model_validate({
            "name": "Kim Minjun",
            "relationship": "mentor",
            "first_appearance_session": "INT-042",
        })
        assert char.first_appearance_session == "INT-042"

    @pytest.mark.unit
    @pytest.mark.schema
    def test_character_defaults(self) -> None:
        char = CharacterEntry.model_validate({
            "name": "Kim Minjun",
            "relationship": "mentor",
        })
        assert char.aliases == []
        assert char.description == ""
        assert char.years_active == []
        assert char.first_appearance_session is None


# ──────────────────────────────────────────────
# LocationEntry Tests
# ──────────────────────────────────────────────


class TestLocationEntry:
    """Tests for individual location entries."""

    @pytest.mark.unit
    @pytest.mark.schema
    def test_valid_location(self, valid_location_data: dict[str, Any]) -> None:
        loc = LocationEntry.model_validate(valid_location_data)
        assert loc.name == "Seoul National University"
        assert loc.city == "Seoul"

    @pytest.mark.unit
    @pytest.mark.schema
    def test_location_minimal(self) -> None:
        loc = LocationEntry.model_validate({"name": "Home"})
        assert loc.city == ""
        assert loc.country == ""
        assert loc.years_relevant == []

    @pytest.mark.unit
    @pytest.mark.schema
    def test_location_missing_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LocationEntry.model_validate({"city": "Seoul"})


# ──────────────────────────────────────────────
# EventEntry Tests
# ──────────────────────────────────────────────


class TestEventEntry:
    """Tests for individual event entries."""

    @pytest.mark.unit
    @pytest.mark.schema
    def test_valid_event(self, valid_event_data: dict[str, Any]) -> None:
        event = EventEntry.model_validate(valid_event_data)
        assert event.significance == EventSignificance.MILESTONE
        assert "INT-001" in event.interview_refs

    @pytest.mark.unit
    @pytest.mark.schema
    def test_event_description_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 5"):
            EventEntry.model_validate({"description": "Hi"})

    @pytest.mark.unit
    @pytest.mark.schema
    def test_event_invalid_significance(self) -> None:
        with pytest.raises(ValidationError):
            EventEntry.model_validate({
                "description": "Some event happened",
                "significance": "catastrophic",
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_event_defaults(self) -> None:
        event = EventEntry.model_validate({"description": "Some event happened"})
        assert event.significance == EventSignificance.BACKGROUND
        assert event.interview_refs == []
        assert event.characters_involved == []


# ──────────────────────────────────────────────
# StoryBibleEntry Tests
# ──────────────────────────────────────────────


class TestStoryBibleEntry:
    """Tests for the top-level story bible container."""

    @pytest.mark.unit
    @pytest.mark.schema
    def test_valid_story_bible(self, valid_story_bible_data: dict[str, Any]) -> None:
        bible = StoryBibleEntry.model_validate(valid_story_bible_data)
        assert bible.subject_name == "Park Jihoon"
        assert len(bible.characters) == 1
        assert len(bible.locations) == 1
        assert len(bible.events) == 1

    @pytest.mark.unit
    @pytest.mark.schema
    def test_story_bible_invalid_version_format(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_story_bible_data)
        data["version"] = "v1.0"
        with pytest.raises(ValidationError, match="String should match pattern"):
            StoryBibleEntry.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_timeline_start_after_end_rejected(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_story_bible_data)
        data["timeline_start_year"] = 2030
        data["timeline_end_year"] = 1990
        with pytest.raises(ValidationError, match="timeline_start_year"):
            StoryBibleEntry.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_timeline_same_year_accepted(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_story_bible_data)
        data["timeline_start_year"] = 2000
        data["timeline_end_year"] = 2000
        bible = StoryBibleEntry.model_validate(data)
        assert bible.timeline_start_year == bible.timeline_end_year

    @pytest.mark.unit
    @pytest.mark.schema
    def test_duplicate_character_names_rejected(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_story_bible_data)
        data["characters"].append({
            "name": "Kim Minjun",
            "relationship": "colleague",
        })
        with pytest.raises(ValidationError, match="Duplicate character names"):
            StoryBibleEntry.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_event_references_nonexistent_character(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_story_bible_data)
        data["events"][0]["characters_involved"] = ["Ghost Person"]
        with pytest.raises(ValidationError, match="not found in characters list"):
            StoryBibleEntry.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_event_references_character_by_alias(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        """An event can reference a character by alias, not just primary name."""
        data = copy.deepcopy(valid_story_bible_data)
        data["events"][0]["characters_involved"] = ["MJ"]
        bible = StoryBibleEntry.model_validate(data)
        assert bible.events[0].characters_involved == ["MJ"]

    @pytest.mark.unit
    @pytest.mark.schema
    def test_empty_characters_list_accepted(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_story_bible_data)
        data["characters"] = []
        data["events"] = []  # Remove events too (they reference characters)
        bible = StoryBibleEntry.model_validate(data)
        assert bible.characters == []

    @pytest.mark.unit
    @pytest.mark.schema
    def test_year_boundary_values(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_story_bible_data)
        data["timeline_start_year"] = 1900
        data["timeline_end_year"] = 2100
        bible = StoryBibleEntry.model_validate(data)
        assert bible.timeline_start_year == 1900

    @pytest.mark.unit
    @pytest.mark.schema
    def test_year_below_minimum_rejected(
        self, valid_story_bible_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_story_bible_data)
        data["timeline_start_year"] = 1899
        with pytest.raises(ValidationError):
            StoryBibleEntry.model_validate(data)
