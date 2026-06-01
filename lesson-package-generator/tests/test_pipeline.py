"""Pipeline tests — placeholder mode."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.orchestrator import (  # noqa: E402
    GATE_AFTER_LESSON_PLAN,
    build_intake,
    run_pipeline,
)
from scripts.pipeline_options import PipelineOptions, RunSupplementary  # noqa: E402


@pytest.fixture
def isolated_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LESSON_PACKAGE_PLACEHOLDER", "1")
    state_src = ROOT / "state.yaml"
    if state_src.is_file():
        (tmp_path / "state.yaml").write_text(state_src.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def _intake() -> dict:
    return build_intake(
        body_text="요 3:16",
        audience="중고등부",
        volume="90",
        emphasis="은혜 강조",
    )


def _opts(**kwargs: object) -> PipelineOptions:
    return PipelineOptions(auto_approve=True, **kwargs)


def test_lesson_plan_only(isolated_project: Path) -> None:
    result = run_pipeline(_intake(), isolated_project, _opts())
    assert result["status"] == "completed"
    assert (isolated_project / "outputs" / "lesson_plan" / "lesson_plan.json").is_file()
    manifest = json.loads(
        (isolated_project / "outputs" / "package" / "lesson_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["skipped"]["teaching"] is True
    assert "lesson_plan" in manifest["artifacts"]


def test_full_supplementary(isolated_project: Path) -> None:
    result = run_pipeline(
        _intake(),
        isolated_project,
        _opts(
            run_supplementary=RunSupplementary(teaching=True, praise=True, promo=True),
        ),
    )
    assert result["status"] == "completed"
    assert (isolated_project / "outputs" / "teaching" / "teaching_materials.json").is_file()
    assert (isolated_project / "outputs" / "praise" / "praise_package.json").is_file()
    assert (isolated_project / "outputs" / "promo" / "promo_video_spec.json").is_file()


def test_human_gate_pauses_before_supplementary(isolated_project: Path) -> None:
    result = run_pipeline(
        _intake(),
        isolated_project,
        PipelineOptions(
            run_supplementary=RunSupplementary(teaching=True),
            auto_approve=False,
            skip_human_gates=False,
        ),
    )
    # First gate is after_intake — pipeline stops before step1 unless user approves all gates
    assert result["status"] == "waiting_human"

    # With only lesson-plan gate bypassed we need both gates approved for full run;
    # after_intake blocks first — verify pending gate
    assert result["pending_gate"] in ("after_intake", GATE_AFTER_LESSON_PLAN)


def test_human_gate_after_lesson_plan(
    isolated_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Approve intake only; pause before supplementary steps."""
    from scripts import orchestrator as orch

    opts = PipelineOptions(
        run_supplementary=RunSupplementary(teaching=True),
        skip_human_gates=False,
        auto_approve=False,
    )

    def fake_gate(gate_id: str, message: str, options: PipelineOptions) -> bool:
        return gate_id == orch.GATE_AFTER_INTAKE

    monkeypatch.setattr(orch, "_require_human_gate", fake_gate)
    result = run_pipeline(_intake(), isolated_project, opts)

    assert result["status"] == "waiting_human"
    assert result["pending_gate"] == GATE_AFTER_LESSON_PLAN
    assert (isolated_project / "outputs" / "lesson_plan" / "lesson_plan.json").is_file()
    assert not (isolated_project / "outputs" / "teaching" / "teaching_materials.json").exists()
