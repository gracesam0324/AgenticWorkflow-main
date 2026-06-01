"""Tests for promo-video.v1."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.modules import step2_teaching, step3_praise, step4_promo  # noqa: E402
from scripts.promo_contract import FORMAT_VERSION, validate_promo_package  # noqa: E402


@pytest.fixture
def prior_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LESSON_PACKAGE_PLACEHOLDER", "1")
    intake = {
        "body_text": "하나님이 세상을 사랑하사",
        "theme": "수련회 초대",
        "audience": "중등부",
        "volume": "45",
        "emphasis": "수련회",
        "locale": "ko",
    }
    tdir = tmp_path / "teaching"
    pdir = tmp_path / "praise"
    step2_teaching.run(intake, tdir, lesson_plan=None)
    step3_praise.run(intake, pdir, teaching_dir=tdir)
    return tmp_path


def test_promo_package(prior_outputs: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LESSON_PACKAGE_PLACEHOLDER", "1")
    promo_dir = prior_outputs / "promo"
    intake = {
        "body_text": "하나님이 세상을 사랑하사",
        "theme": "수련회 초대",
        "audience": "중등부",
        "emphasis": "수련회",
    }
    result = step4_promo.run(
        intake,
        promo_dir,
        teaching_dir=prior_outputs / "teaching",
        praise_dir=prior_outputs / "praise",
        assemble=False,
    )

    assert result["format"] == FORMAT_VERSION
    pkg = json.loads((promo_dir / "promo_video.v1.json").read_text(encoding="utf-8"))
    assert not validate_promo_package(pkg)
    total = pkg["meta"]["total_duration_seconds"]
    assert 30 <= total <= 45
    assert (promo_dir / "storyboard.json").is_file()
    assert (promo_dir / "subtitles.srt").is_file()
    assert (promo_dir / "narration_script.md").is_file()
    cuts = pkg["storyboard"]["cuts"]
    assert all(c.get("video_prompt") for c in cuts)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_assemble_with_placeholders(prior_outputs: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LESSON_PACKAGE_PLACEHOLDER", "1")
    promo_dir = prior_outputs / "promo"
    intake = {"theme": "수련회", "body_text": "", "audience": "중등부", "emphasis": "수련회"}
    step4_promo.run(
        intake,
        promo_dir,
        teaching_dir=prior_outputs / "teaching",
        praise_dir=prior_outputs / "praise",
        assemble=False,
    )
    from scripts.assemble_promo_video import assemble

    out = assemble(promo_dir, music_path=None, skip_tts=True)
    assert out.is_file()
    assert out.stat().st_size > 1000
