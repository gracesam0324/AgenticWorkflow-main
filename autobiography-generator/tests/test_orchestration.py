"""Tests for orchestration infrastructure — state.yaml v2.0, SOT library, phase routing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.schemas import OrchestrationSection, StateFileV2
from scripts.sot_lib import load_state, save_state, update_state_yaml


# ──────────────────────────────────────────────
# StateFileV2 Pydantic Model Tests
# ──────────────────────────────────────────────


class TestStateFileV2:
    """Test v2.0 state file schema."""

    def test_valid_state_v2(self, valid_state_v2_data: dict[str, Any]):
        """StateFileV2 accepts valid v2.0 data."""
        state = StateFileV2.model_validate(valid_state_v2_data)
        assert state.orchestration.version == "2.0"
        assert state.orchestration.current_phase == "build"
        assert state.workflow["name"] == "AI Autobiography Generator"

    def test_missing_workflow_keys_rejected(self, valid_state_v2_data: dict[str, Any]):
        """StateFileV2 rejects workflow section missing required keys."""
        del valid_state_v2_data["workflow"]["name"]
        with pytest.raises(ValueError, match="missing required keys"):
            StateFileV2.model_validate(valid_state_v2_data)

    def test_orchestration_defaults(self):
        """OrchestrationSection provides sensible defaults."""
        orch = OrchestrationSection()
        assert orch.version == "2.0"
        assert orch.current_phase == "build"
        assert orch.current_substep is None
        assert orch.fallback["current_tier"] == 2
        assert orch.rlm["session_count"] == 0

    def test_v1_fields_preserved(self, valid_state_v2_data: dict[str, Any]):
        """All v1.0 workflow fields survive v2.0 validation."""
        state = StateFileV2.model_validate(valid_state_v2_data)
        wf = state.workflow
        assert wf["status"] == "not_started"
        assert wf["parent_genome"]["source"] == "AgenticWorkflow"
        assert len(wf["parent_genome"]["inherited_dna"]) >= 8
        assert wf["book_config"]["language"] == "ko"

    def test_orchestration_phase_values(self, valid_state_v2_data: dict[str, Any]):
        """Orchestration phase tracks correctly."""
        valid_state_v2_data["orchestration"]["current_phase"] = "implementation"
        valid_state_v2_data["orchestration"]["current_substep"] = "7c"
        state = StateFileV2.model_validate(valid_state_v2_data)
        assert state.orchestration.current_phase == "implementation"
        assert state.orchestration.current_substep == "7c"


# ──────────────────────────────────────────────
# SOT Library Tests (sot_lib.py)
# ──────────────────────────────────────────────


class TestSOTLibrary:
    """Test atomic read/write operations for SOT."""

    def test_save_and_load(self, tmp_path: Path):
        """Save and load round-trip preserves data."""
        sot_path = tmp_path / "state.yaml"
        data = {"workflow": {"name": "test", "status": "ok"}}
        save_state(data, sot_path)
        loaded = load_state(sot_path)
        assert loaded["workflow"]["name"] == "test"
        assert loaded["workflow"]["status"] == "ok"

    def test_save_creates_backup(self, tmp_path: Path):
        """Save creates .bak file for crash recovery."""
        sot_path = tmp_path / "state.yaml"
        # Write initial
        save_state({"v": 1}, sot_path)
        # Write again — should create .bak
        save_state({"v": 2}, sot_path)
        bak_path = Path(str(sot_path) + ".bak")
        assert bak_path.exists()
        with open(bak_path) as f:
            bak_data = yaml.safe_load(f)
        assert bak_data["v"] == 1  # .bak has previous version

    def test_load_recovers_from_backup(self, tmp_path: Path):
        """Load falls back to .bak when main file is corrupted."""
        sot_path = tmp_path / "state.yaml"
        bak_path = Path(str(sot_path) + ".bak")
        # Write good backup
        with open(bak_path, "w") as f:
            yaml.dump({"recovered": True}, f)
        # Write corrupted main
        with open(sot_path, "w") as f:
            f.write("{ this is not: valid: yaml: [")
        loaded = load_state(sot_path)
        assert loaded["recovered"] is True

    def test_load_raises_when_no_backup(self, tmp_path: Path):
        """Load raises when both main and backup are missing."""
        sot_path = tmp_path / "nonexistent.yaml"
        with pytest.raises((FileNotFoundError, OSError)):
            load_state(sot_path)

    def test_update_state_yaml_workflow_key(self, tmp_path: Path):
        """update_state_yaml modifies nested workflow keys."""
        sot_path = tmp_path / "state.yaml"
        save_state({
            "workflow": {"name": "test", "status": "not_started", "chapters": {}},
            "orchestration": {"version": "2.0"},
        }, sot_path)
        update_state_yaml("chapters.ch-1", sot_path, status="drafting", draft_version=1)
        loaded = load_state(sot_path)
        assert loaded["workflow"]["chapters"]["ch-1"]["status"] == "drafting"
        assert loaded["workflow"]["chapters"]["ch-1"]["draft_version"] == 1

    def test_update_state_yaml_orchestration_key(self, tmp_path: Path):
        """update_state_yaml modifies orchestration section directly."""
        sot_path = tmp_path / "state.yaml"
        save_state({
            "workflow": {"name": "test"},
            "orchestration": {"version": "2.0", "current_phase": "build"},
        }, sot_path)
        update_state_yaml("orchestration", sot_path, current_phase="research")
        loaded = load_state(sot_path)
        assert loaded["orchestration"]["current_phase"] == "research"

    def test_save_creates_parent_dirs(self, tmp_path: Path):
        """Save creates parent directories if needed."""
        sot_path = tmp_path / "nested" / "deep" / "state.yaml"
        save_state({"ok": True}, sot_path)
        assert sot_path.exists()
        loaded = load_state(sot_path)
        assert loaded["ok"] is True


# ──────────────────────────────────────────────
# Quality Gate Check Tests
# ──────────────────────────────────────────────


class TestQualityGateCheck:
    """Test quality_gate_check.py check functions."""

    def test_check_schemas_valid(self, project_dir_with_state: Path):
        """Schema validation passes with valid JSON schemas."""
        from scripts.quality_gate_check import check_schemas_valid

        schema_dir = project_dir_with_state / "schemas"
        (schema_dir / "test.json").write_text('{"type": "object"}')
        result = check_schemas_valid(project_dir_with_state)
        assert result.passed
        assert result.check_id == "SCHEMA-VALID"

    def test_check_schemas_invalid(self, project_dir_with_state: Path):
        """Schema validation fails with invalid JSON."""
        from scripts.quality_gate_check import check_schemas_valid

        schema_dir = project_dir_with_state / "schemas"
        (schema_dir / "bad.json").write_text("{not valid json")
        result = check_schemas_valid(project_dir_with_state)
        assert not result.passed

    def test_check_scripts_syntax(self, project_dir_with_state: Path):
        """Script syntax check passes with valid Python."""
        from scripts.quality_gate_check import check_scripts_syntax

        scripts_dir = project_dir_with_state / "scripts"
        (scripts_dir / "good.py").write_text("x = 1\n")
        result = check_scripts_syntax(project_dir_with_state)
        assert result.passed

    def test_check_scripts_syntax_fails(self, project_dir_with_state: Path):
        """Script syntax check fails with invalid Python."""
        from scripts.quality_gate_check import check_scripts_syntax

        scripts_dir = project_dir_with_state / "scripts"
        (scripts_dir / "bad.py").write_text("def broken(:\n")
        result = check_scripts_syntax(project_dir_with_state)
        assert not result.passed

    def test_get_checks_for_step(self):
        """Step-to-check mapping returns appropriate checks."""
        from scripts.quality_gate_check import get_checks_for_step

        build_checks = get_checks_for_step("0.5a")
        assert "check_schemas_valid" in build_checks

        chapter_checks = get_checks_for_step("7c")
        assert "check_chapter_byeonyeokche" in chapter_checks
        assert "check_chapter_emotional_balance" in chapter_checks

    def test_run_checks_all_pass(self, project_dir_with_state: Path):
        """run_checks returns all-pass for valid project."""
        from scripts.quality_gate_check import run_checks

        # Create minimal valid files
        (project_dir_with_state / "schemas" / "test.json").write_text('{"ok": true}')
        (project_dir_with_state / "scripts" / "good.py").write_text("x = 1\n")

        results = run_checks("0.5a", project_dir_with_state)
        # check_tests_pass will fail (no tests), but schemas and syntax should pass
        schema_result = next(r for r in results if r.check_id == "SCHEMA-VALID")
        syntax_result = next(r for r in results if r.check_id == "SCRIPT-SYNTAX")
        assert schema_result.passed
        assert syntax_result.passed
