"""Tests for praise-worship.v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.modules import step2_teaching, step3_praise  # noqa: E402
from scripts.praise_contract import FORMAT_VERSION, validate_praise_package  # noqa: E402


@pytest.fixture
def teaching_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LESSON_PACKAGE_PLACEHOLDER", "1")
    teaching_dir = tmp_path / "teaching"
    intake = {
        "body_text": "하나님이 세상을 사랑하사",
        "theme": "하나님의 사랑",
        "audience": "중등부",
        "volume": "45",
        "emphasis": "은혜",
        "locale": "ko",
    }
    step2_teaching.run(intake, teaching_dir, lesson_plan=None)
    return teaching_dir


def test_praise_from_teaching(teaching_output: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LESSON_PACKAGE_PLACEHOLDER", "1")
    praise_dir = tmp_path / "praise"
    intake = {
        "body_text": "하나님이 세상을 사랑하사",
        "theme": "하나님의 사랑",
        "audience": "중등부",
        "emphasis": "은혜",
    }
    result = step3_praise.run(
        intake, praise_dir, teaching_dir=teaching_output
    )

    assert result["format"] == FORMAT_VERSION
    assert (praise_dir / "praise_worship.v1.json").is_file()
    assert (praise_dir / "lyrics" / "full_lyrics.md").is_file()
    assert (praise_dir / "music" / "suno_prompt.txt").is_file()
    assert (praise_dir / "music" / "music_prompt.json").is_file()

    pkg = json.loads((praise_dir / "praise_worship.v1.json").read_text(encoding="utf-8"))
    assert not validate_praise_package(pkg)
    assert pkg["song"]["lyrics"]["chorus"]["lines"]
    assert pkg["music_generation"]["prompt_structured"]["bpm"]

    suno = (praise_dir / "music" / "suno_prompt.txt").read_text(encoding="utf-8")
    assert "BPM" in suno or "bpm" in suno.lower() or str(pkg["music_generation"]["prompt_structured"]["bpm"]) in suno

    downstream = json.loads(
        (praise_dir / "praise_worship.downstream.json").read_text(encoding="utf-8")
    )
    assert downstream["format"] == FORMAT_VERSION
    assert downstream["suno_prompt"]
