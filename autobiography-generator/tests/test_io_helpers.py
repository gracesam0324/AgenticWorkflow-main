"""Tests for YAML I/O helpers (load_yaml, save_yaml).

Covers:
- Loading valid YAML files
- Handling missing files
- Handling empty files
- Handling invalid YAML syntax
- Round-trip (save then load)
- Validation errors on load
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from scripts.schemas import StoryBibleEntry, load_yaml, save_yaml


class TestLoadYaml:
    """Tests for the load_yaml helper."""

    @pytest.mark.integration
    @pytest.mark.schema
    def test_load_valid_story_bible(
        self,
        story_bible_yaml_file: Path,
    ) -> None:
        bible = load_yaml(story_bible_yaml_file, StoryBibleEntry)
        assert isinstance(bible, StoryBibleEntry)
        assert bible.subject_name == "Park Jihoon"

    @pytest.mark.integration
    @pytest.mark.schema
    def test_load_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError, match="File not found"):
            load_yaml("/nonexistent/path.yaml", StoryBibleEntry)

    @pytest.mark.integration
    @pytest.mark.schema
    def test_load_empty_file(self, empty_yaml_file: Path) -> None:
        with pytest.raises(ValueError, match="File is empty"):
            load_yaml(empty_yaml_file, StoryBibleEntry)

    @pytest.mark.integration
    @pytest.mark.schema
    def test_load_invalid_yaml(self, invalid_yaml_file: Path) -> None:
        with pytest.raises(yaml.YAMLError):
            load_yaml(invalid_yaml_file, StoryBibleEntry)

    @pytest.mark.integration
    @pytest.mark.schema
    def test_load_valid_yaml_invalid_schema(
        self,
        tmp_path: Path,
    ) -> None:
        """Valid YAML that does not match the schema."""
        filepath = tmp_path / "bad-schema.yaml"
        with open(filepath, "w") as f:
            yaml.dump({"wrong": "data"}, f)
        with pytest.raises(ValidationError):
            load_yaml(filepath, StoryBibleEntry)


class TestSaveYaml:
    """Tests for the save_yaml helper."""

    @pytest.mark.integration
    @pytest.mark.schema
    def test_save_creates_file(
        self,
        tmp_path: Path,
        valid_story_bible_data: dict[str, Any],
    ) -> None:
        bible = StoryBibleEntry.model_validate(valid_story_bible_data)
        filepath = save_yaml(tmp_path / "output.yaml", bible)
        assert filepath.exists()

    @pytest.mark.integration
    @pytest.mark.schema
    def test_save_creates_parent_dirs(
        self,
        tmp_path: Path,
        valid_story_bible_data: dict[str, Any],
    ) -> None:
        bible = StoryBibleEntry.model_validate(valid_story_bible_data)
        filepath = save_yaml(tmp_path / "deep" / "nested" / "output.yaml", bible)
        assert filepath.exists()

    @pytest.mark.integration
    @pytest.mark.schema
    def test_round_trip_preserves_data(
        self,
        tmp_path: Path,
        valid_story_bible_data: dict[str, Any],
    ) -> None:
        """Save and reload should produce equivalent data."""
        original = StoryBibleEntry.model_validate(valid_story_bible_data)
        filepath = save_yaml(tmp_path / "roundtrip.yaml", original)
        loaded = load_yaml(filepath, StoryBibleEntry)

        assert isinstance(loaded, StoryBibleEntry)
        assert loaded.subject_name == original.subject_name
        assert loaded.version == original.version
        assert len(loaded.characters) == len(original.characters)
        assert len(loaded.events) == len(original.events)
        assert loaded.timeline_start_year == original.timeline_start_year

    @pytest.mark.integration
    @pytest.mark.schema
    def test_saved_file_is_valid_yaml(
        self,
        tmp_path: Path,
        valid_story_bible_data: dict[str, Any],
    ) -> None:
        bible = StoryBibleEntry.model_validate(valid_story_bible_data)
        filepath = save_yaml(tmp_path / "check.yaml", bible)
        with open(filepath) as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert data["subject_name"] == "Park Jihoon"
