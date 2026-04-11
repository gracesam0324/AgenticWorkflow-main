"""Tests for Korean-specific validators — embellishment, metaphor, emotional balance (§22.7)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


# ──────────────────────────────────────────────
# Embellishment Validator Tests
# ──────────────────────────────────────────────


class TestValidateEmbellishment:
    """Test validate_embellishment.py — [INFERRED] tag counting + cap enforcement."""

    def test_no_inferred_tags(self):
        """Text with no [INFERRED] tags returns 0 count."""
        from scripts.validate_embellishment import count_inferred_tags

        text = "이것은 순수한 텍스트입니다. 인터뷰에서 직접 나온 내용입니다."
        count = count_inferred_tags(text)
        assert count == 0

    def test_inferred_tag_counting(self):
        """[INFERRED] tags are correctly counted."""
        from scripts.validate_embellishment import count_inferred_tags

        text = """이것은 첫 번째 문장입니다.
[INFERRED] 이것은 추론된 내용입니다.
이것은 세 번째 문장입니다.
[INFERRED] 이것도 추론된 내용입니다.
이것은 다섯 번째 문장입니다."""
        count = count_inferred_tags(text)
        assert count == 2

    def test_validate_within_cap(self, tmp_path: Path):
        """Chapter within embellishment cap passes validation."""
        from scripts.validate_embellishment import validate_embellishment

        chapter = tmp_path / "ch01.md"
        chapter.write_text("일반 문장입니다.\n[INFERRED] 추론 문장입니다.\n또 다른 일반 문장입니다.\n네 번째 문장.\n다섯 번째 문장.")
        result = validate_embellishment(chapter, cap=0.5)
        assert result.get("passed", result.get("ok", True))

    def test_validate_exceeds_cap(self, tmp_path: Path):
        """Chapter exceeding embellishment cap fails validation."""
        from scripts.validate_embellishment import validate_embellishment

        chapter = tmp_path / "ch01.md"
        chapter.write_text("[INFERRED] 추론 1.\n[INFERRED] 추론 2.\n[INFERRED] 추론 3.\n일반 문장.")
        result = validate_embellishment(chapter, cap=0.05)
        assert not result.get("passed", result.get("ok", False))

    def test_count_sentences(self):
        """Sentence counting works with multi-word sentences."""
        from scripts.validate_embellishment import count_sentences

        text = "This is the first sentence here. This is the second sentence here. This is the third one too."
        count = count_sentences(text)
        assert count >= 3


# ──────────────────────────────────────────────
# Metaphor Validator Tests
# ──────────────────────────────────────────────


class TestValidateMetaphor:
    """Test validate_metaphor.py — controlling metaphor ≥3 chapters presence."""

    def test_metaphor_found_in_chapter(self, tmp_path: Path):
        """check_metaphor_in_chapter detects metaphor in file."""
        from scripts.validate_metaphor import check_metaphor_in_chapter

        chapter = tmp_path / "ch01.md"
        chapter.write_text("바다가 보이는 언덕에서 바라보았다.")
        # Function takes (chapter_path: Path, metaphor: str)
        assert check_metaphor_in_chapter(chapter, "바다")

    def test_metaphor_not_found(self, tmp_path: Path):
        """check_metaphor_in_chapter returns False when absent."""
        from scripts.validate_metaphor import check_metaphor_in_chapter

        chapter = tmp_path / "ch01.md"
        chapter.write_text("산 위의 풍경을 바라보았다.")
        assert not check_metaphor_in_chapter(chapter, "바다")

    def test_find_chapter_files(self, tmp_path: Path):
        """find_chapter_files finds chapter .md files."""
        from scripts.validate_metaphor import find_chapter_files

        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        (chapters_dir / "ch01_draft_v1.md").write_text("content")
        (chapters_dir / "ch02_draft_v1.md").write_text("content")
        files = find_chapter_files(chapters_dir)
        assert len(files) >= 2


# ──────────────────────────────────────────────
# Emotional Balance Validator Tests
# ──────────────────────────────────────────────


class TestValidateEmotionalBalance:
    """Test validate_emotional_balance.py — 한-흥-정 keyword counting."""

    def _load_keywords(self, config_path: Path) -> dict[str, list[str]]:
        """Helper to convert config format to keywords dict."""
        config = yaml.safe_load(config_path.read_text())
        keywords = {}
        for emotion, data in config.items():
            if isinstance(data, dict) and "keywords" in data:
                keywords[emotion] = data["keywords"]
        return keywords

    def test_counts_han_keywords(self, emotion_keywords_config: Path):
        """Han (한) keywords are correctly counted."""
        from scripts.validate_emotional_balance import count_emotion_keywords

        text = "그리움이 밀려왔다. 아픔을 참으며 눈물을 흘렸다."
        keywords = self._load_keywords(emotion_keywords_config)
        counts = count_emotion_keywords(text, keywords)
        assert counts["han"] >= 3  # 그리움, 아픔, 눈물

    def test_counts_heung_keywords(self, emotion_keywords_config: Path):
        """Heung (흥) keywords are correctly counted."""
        from scripts.validate_emotional_balance import count_emotion_keywords

        text = "기쁨에 가득 찬 웃음소리가 울려 퍼졌다."
        keywords = self._load_keywords(emotion_keywords_config)
        counts = count_emotion_keywords(text, keywords)
        assert counts["heung"] >= 2  # 기쁨, 웃음

    def test_counts_jeong_keywords(self, emotion_keywords_config: Path):
        """Jeong (정) keywords are correctly counted."""
        from scripts.validate_emotional_balance import count_emotion_keywords

        text = "따뜻한 사랑이 느껴지는 다정한 손길이었다."
        keywords = self._load_keywords(emotion_keywords_config)
        counts = count_emotion_keywords(text, keywords)
        assert counts["jeong"] >= 3  # 따뜻, 사랑, 다정

    def test_empty_text_returns_zeros(self, emotion_keywords_config: Path):
        """Empty text returns zero counts."""
        from scripts.validate_emotional_balance import count_emotion_keywords

        keywords = self._load_keywords(emotion_keywords_config)
        counts = count_emotion_keywords("", keywords)
        assert counts["han"] == 0
        assert counts["heung"] == 0
        assert counts["jeong"] == 0

    def test_imbalanced_detected(self):
        """Severely imbalanced emotions are detected."""
        from scripts.validate_emotional_balance import assess_balance

        # All han, no heung or jeong → severely imbalanced
        result = assess_balance({"han": 20, "heung": 0, "jeong": 0}, min_share=0.1, max_share=0.8)
        assert not result["balanced"]

    def test_balanced_emotions_pass(self):
        """Reasonably balanced emotions pass."""
        from scripts.validate_emotional_balance import assess_balance

        result = assess_balance({"han": 5, "heung": 4, "jeong": 6}, min_share=0.1, max_share=0.8)
        assert result["balanced"]
