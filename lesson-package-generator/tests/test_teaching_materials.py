"""Tests for teaching-materials.v1 generation and file output."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.modules import step2_teaching  # noqa: E402
from scripts.teaching_contract import FORMAT_VERSION, validate_teaching_package  # noqa: E402


@pytest.fixture
def teaching_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LESSON_PACKAGE_PLACEHOLDER", "1")
    out = tmp_path / "teaching"
    out.mkdir()
    return out


def test_generates_files(teaching_dir: Path) -> None:
    intake = {
        "body_text": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니",
        "theme": "하나님의 사랑",
        "audience": "중등부",
        "volume": "45",
        "emphasis": "은혜",
        "locale": "ko",
    }
    result = step2_teaching.run(intake, teaching_dir, lesson_plan=None)

    assert result["format"] == FORMAT_VERSION
    assert (teaching_dir / "teaching_materials.v1.json").is_file()
    assert (teaching_dir / "print" / "worksheet.html").is_file()
    assert (teaching_dir / "slides" / "slides.html").is_file()
    assert (teaching_dir / "teaching_materials.downstream.json").is_file()
    assert (teaching_dir / "teaching_materials.manifest.json").is_file()

    pkg = json.loads((teaching_dir / "teaching_materials.v1.json").read_text(encoding="utf-8"))
    assert not validate_teaching_package(pkg)

    html = (teaching_dir / "print" / "worksheet.html").read_text(encoding="utf-8")
    assert "[IMG:" in html or "IMAGE" in html

    downstream = json.loads(
        (teaching_dir / "teaching_materials.downstream.json").read_text(encoding="utf-8")
    )
    assert downstream["format"] == FORMAT_VERSION
    assert downstream["discussion_questions"]
