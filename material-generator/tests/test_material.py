"""Tests for material-generator (teaching-materials.v1) — standalone module."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parent
for _p in (str(MODULE_ROOT), str(REPO_ROOT / "content-common")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from material_generator import (  # noqa: E402
    FORMAT_VERSION,
    run,
    validate_material_package,
)


@pytest.fixture
def teaching_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("CONTENT_PLACEHOLDER", "1")
    out = tmp_path / "teaching"
    out.mkdir()
    return out


def _intake() -> dict:
    return {
        "body_text": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니",
        "theme": "하나님의 사랑",
        "audience": "중등부",
        "volume": "45",
        "emphasis": "은혜",
        "locale": "ko",
    }


def test_standalone_generates_files(teaching_dir: Path) -> None:
    """단독 실행: 본문·테마·대상만으로 (lesson_plan 없이) 생성."""
    result = run(_intake(), teaching_dir, lesson_plan=None)

    assert result["format"] == FORMAT_VERSION
    assert (teaching_dir / "teaching_materials.v1.json").is_file()
    assert (teaching_dir / "print" / "worksheet.html").is_file()
    assert (teaching_dir / "slides" / "slides.html").is_file()
    assert (teaching_dir / "teaching_materials.downstream.json").is_file()

    pkg = json.loads((teaching_dir / "teaching_materials.v1.json").read_text(encoding="utf-8"))
    assert not validate_material_package(pkg)

    downstream = json.loads(
        (teaching_dir / "teaching_materials.downstream.json").read_text(encoding="utf-8")
    )
    assert downstream["format"] == FORMAT_VERSION
    assert downstream["discussion_questions"]


def test_consumes_lesson_plan_key_message(teaching_dir: Path) -> None:
    """lesson_plan이 주어지면 핵심메시지를 소비(정합)."""
    plan = {"step_id": "step1_lesson_plan", "sections": {"key_message": "자유는 본문의 약속이다"}}
    result = run(_intake(), teaching_dir, lesson_plan=plan)
    assert result["package"]["summary"]["key_message"] == "자유는 본문의 약속이다"
