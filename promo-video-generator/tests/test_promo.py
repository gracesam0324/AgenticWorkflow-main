"""Tests for promo-video-generator (promo-video.v1) — standalone module."""

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

from promo_video_generator import FORMAT_VERSION, run, validate_promo_video_package  # noqa: E402


@pytest.fixture(autouse=True)
def _placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_PLACEHOLDER", "1")


def test_standalone_without_upstream(tmp_path: Path) -> None:
    """단독 실행: 교보재·찬양 없이 테마·대상만으로 홍보영상 생성."""
    intake = {"theme": "중등 수련회", "body_text": "", "audience": "중등부", "emphasis": "수련회"}
    promo_dir = tmp_path / "promo"
    result = run(intake, promo_dir, lesson_plan=None)

    assert result["format"] == FORMAT_VERSION
    assert (promo_dir / "promo_video.v1.json").is_file()
    assert (promo_dir / "storyboard.json").is_file()
    assert (promo_dir / "subtitles.srt").is_file()

    pkg = json.loads((promo_dir / "promo_video.v1.json").read_text(encoding="utf-8"))
    assert not validate_promo_video_package(pkg)
    total = pkg["meta"]["total_duration_seconds"]
    assert 30 <= total <= 45
    assert all(c.get("video_prompt") for c in pkg["storyboard"]["cuts"])
