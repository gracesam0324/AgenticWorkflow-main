"""Tests for anthem-generator (praise-worship.v1) — standalone module."""

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

from anthem_generator import FORMAT_VERSION, run, validate_anthem_package  # noqa: E402


@pytest.fixture(autouse=True)
def _placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_PLACEHOLDER", "1")


def _intake() -> dict:
    return {
        "body_text": "누가복음 8:26-39",
        "theme": "자유",
        "audience": "중등부",
        "emphasis": "자유",
        "volume": "45",
        "locale": "ko",
    }


def test_standalone_without_teaching(tmp_path: Path) -> None:
    """단독 실행: 교보재 없이 본문·테마·대상만으로 찬양 생성."""
    praise_dir = tmp_path / "praise"
    result = run(_intake(), praise_dir, lesson_plan=None)

    assert result["format"] == FORMAT_VERSION
    assert (praise_dir / "praise_worship.v1.json").is_file()
    assert (praise_dir / "lyrics" / "full_lyrics.md").is_file()
    assert (praise_dir / "music" / "suno_prompt.txt").is_file()

    pkg = json.loads((praise_dir / "praise_worship.v1.json").read_text(encoding="utf-8"))
    assert not validate_anthem_package(pkg)
    assert pkg["song"]["lyrics"]["chorus"]["lines"]


def test_lesson_plan_key_message_alignment(tmp_path: Path) -> None:
    plan = {"step_id": "step1_lesson_plan", "sections": {"key_message": "자유는 본문의 약속이다"}}
    result = run(_intake(), tmp_path / "praise", lesson_plan=plan)
    assert result["package"]["inputs"]["key_message"] == "자유는 본문의 약속이다"
