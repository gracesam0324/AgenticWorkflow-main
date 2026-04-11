"""Tests for ChapterDraft schema validation.

Covers:
- Valid chapter construction
- Word count deviation enforcement
- Time period validation
- Interview ref format validation
- Section structure requirements
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.schemas import ChapterDraft, ChapterSection, ChapterStatus


class TestChapterSection:
    """Tests for individual chapter sections."""

    @pytest.mark.unit
    @pytest.mark.schema
    def test_valid_section(self, valid_chapter_section_data: dict[str, Any]) -> None:
        section = ChapterSection.model_validate(valid_chapter_section_data)
        assert section.heading == "The First Day"
        assert len(section.interview_refs) == 2

    @pytest.mark.unit
    @pytest.mark.schema
    def test_section_empty_heading_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ChapterSection.model_validate({
                "heading": "",
                "content": "Some content here",
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_section_empty_content_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ChapterSection.model_validate({
                "heading": "Good Heading",
                "content": "",
            })

    @pytest.mark.unit
    @pytest.mark.schema
    def test_section_default_tone(self) -> None:
        section = ChapterSection.model_validate({
            "heading": "A Section",
            "content": "Some content.",
        })
        assert section.emotional_tone.value == "neutral"


class TestChapterDraft:
    """Tests for the full chapter draft schema."""

    @pytest.mark.unit
    @pytest.mark.schema
    def test_valid_chapter(self, valid_chapter_draft_data: dict[str, Any]) -> None:
        chapter = ChapterDraft.model_validate(valid_chapter_draft_data)
        assert chapter.chapter_number == 1
        assert chapter.title == "The Seoul Years"
        assert chapter.status == ChapterStatus.FIRST_DRAFT

    @pytest.mark.unit
    @pytest.mark.schema
    def test_word_count_within_range_accepted(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        """5% deviation is well within the 20% threshold."""
        data = copy.deepcopy(valid_chapter_draft_data)
        data["word_count"] = 4200  # 5% over 4000
        chapter = ChapterDraft.model_validate(data)
        assert chapter.word_count == 4200

    @pytest.mark.unit
    @pytest.mark.schema
    def test_word_count_at_boundary_accepted(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        """Exactly 20% deviation is accepted."""
        data = copy.deepcopy(valid_chapter_draft_data)
        data["word_count"] = 4800  # exactly 20% over 4000
        chapter = ChapterDraft.model_validate(data)
        assert chapter.word_count == 4800

    @pytest.mark.unit
    @pytest.mark.schema
    def test_word_count_over_threshold_rejected(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        """25% deviation exceeds the 20% threshold."""
        data = copy.deepcopy(valid_chapter_draft_data)
        data["word_count"] = 5100  # 27.5% over 4000
        with pytest.raises(ValidationError, match="deviates"):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_word_count_too_low_rejected(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        """Being far under target is also a problem."""
        data = copy.deepcopy(valid_chapter_draft_data)
        data["word_count"] = 2000  # 50% under 4000
        with pytest.raises(ValidationError, match="deviates"):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_time_period_missing_start_rejected(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_chapter_draft_data)
        data["time_period"] = {"end": 1998}
        with pytest.raises(ValidationError, match="'start' and 'end'"):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_time_period_inverted_rejected(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_chapter_draft_data)
        data["time_period"] = {"start": 2000, "end": 1990}
        with pytest.raises(ValidationError, match="must be <= end"):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_invalid_interview_ref_format(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_chapter_draft_data)
        data["interview_refs_used"] = ["SESSION-1", "INT-002"]
        with pytest.raises(ValidationError, match="must match INT-###"):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_empty_interview_refs_rejected(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_chapter_draft_data)
        data["interview_refs_used"] = []
        with pytest.raises(ValidationError):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_no_sections_rejected(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_chapter_draft_data)
        data["sections"] = []
        with pytest.raises(ValidationError):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_chapter_number_zero_rejected(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_chapter_draft_data)
        data["chapter_number"] = 0
        with pytest.raises(ValidationError):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_invalid_status_rejected(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_chapter_draft_data)
        data["status"] = "published"
        with pytest.raises(ValidationError):
            ChapterDraft.model_validate(data)

    @pytest.mark.unit
    @pytest.mark.schema
    def test_all_valid_statuses(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        for status in ["outline", "first-draft", "revised", "reviewed", "final"]:
            data = copy.deepcopy(valid_chapter_draft_data)
            data["status"] = status
            chapter = ChapterDraft.model_validate(data)
            assert chapter.status.value == status

    @pytest.mark.unit
    @pytest.mark.schema
    def test_invalid_story_bible_version_format(
        self, valid_chapter_draft_data: dict[str, Any]
    ) -> None:
        data = copy.deepcopy(valid_chapter_draft_data)
        data["story_bible_version"] = "v1"
        with pytest.raises(ValidationError):
            ChapterDraft.model_validate(data)
