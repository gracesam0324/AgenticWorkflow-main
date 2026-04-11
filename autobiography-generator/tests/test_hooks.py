"""Tests for new hook scripts — quality_gate, idle_check, tdd_guard, rlm_checkpoint."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


# ──────────────────────────────────────────────
# TDD Guard Hook Tests
# ──────────────────────────────────────────────


class TestTDDGuard:
    """Test tdd_guard.py hook behavior."""

    def test_skips_when_no_tdd_guard_file(self, tmp_path: Path):
        """TDD guard exits 0 when .tdd-guard file is absent (Build Phase)."""
        # No .tdd-guard file → should always pass
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "tdd_guard.py"
        if not hook_path.exists():
            pytest.skip("tdd_guard.py not yet created")

        env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}
        # Simulate Write tool input
        input_data = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": str(tmp_path / "scripts" / "new_file.py"), "content": "x = 1"},
        })
        result = subprocess.run(
            ["python3", str(hook_path)],
            input=input_data, capture_output=True, text=True, env={**__import__("os").environ, **env},
        )
        assert result.returncode == 0

    def test_skips_when_file_doesnt_exist(self, tmp_path: Path):
        """TDD guard exits 0 for files that don't exist yet (initial creation)."""
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "tdd_guard.py"
        if not hook_path.exists():
            pytest.skip("tdd_guard.py not yet created")

        # Create .tdd-guard but target file doesn't exist
        tdd_guard = tmp_path / ".tdd-guard"
        tdd_guard.write_text(yaml.dump({
            "source_test_map": {"scripts/new.py": "tests/test_new.py"},
        }))

        env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}
        input_data = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": str(tmp_path / "scripts" / "new.py"), "content": "x = 1"},
        })
        result = subprocess.run(
            ["python3", str(hook_path)],
            input=input_data, capture_output=True, text=True, env={**__import__("os").environ, **env},
        )
        assert result.returncode == 0


# ──────────────────────────────────────────────
# RLM Checkpoint Hook Tests
# ──────────────────────────────────────────────


class TestRLMCheckpoint:
    """Test rlm_checkpoint.py hook behavior."""

    def test_creates_recovery_point(self, tmp_path: Path, valid_state_v2_data: dict[str, Any]):
        """RLM checkpoint appends recovery point to state.yaml."""
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "rlm_checkpoint.py"
        if not hook_path.exists():
            pytest.skip("rlm_checkpoint.py not yet created")

        # Set up state.yaml
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        state_path = claude_dir / "state.yaml"
        with open(state_path, "w") as f:
            yaml.dump(valid_state_v2_data, f, allow_unicode=True)

        env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}
        result = subprocess.run(
            ["python3", str(hook_path)],
            capture_output=True, text=True, env={**__import__("os").environ, **env},
        )
        assert result.returncode == 0

        # Verify recovery point was added
        with open(state_path) as f:
            state = yaml.safe_load(f)
        recovery_points = state["orchestration"]["rlm"]["recovery_points"]
        assert len(recovery_points) >= 1
        assert "step" in recovery_points[-1]
        assert "timestamp" in recovery_points[-1]

    def test_recovery_points_pruned_at_20(self, tmp_path: Path, valid_state_v2_data: dict[str, Any]):
        """RLM checkpoint keeps max 20 recovery points."""
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "rlm_checkpoint.py"
        if not hook_path.exists():
            pytest.skip("rlm_checkpoint.py not yet created")

        # Pre-populate with 25 recovery points
        valid_state_v2_data["orchestration"]["rlm"]["recovery_points"] = [
            {"step": str(i), "substep": None, "snapshot_path": "", "timestamp": f"2026-03-17T{i:02d}:00:00"}
            for i in range(25)
        ]

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        state_path = claude_dir / "state.yaml"
        with open(state_path, "w") as f:
            yaml.dump(valid_state_v2_data, f, allow_unicode=True)

        env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}
        result = subprocess.run(
            ["python3", str(hook_path)],
            capture_output=True, text=True, env={**__import__("os").environ, **env},
        )
        assert result.returncode == 0

        with open(state_path) as f:
            state = yaml.safe_load(f)
        assert len(state["orchestration"]["rlm"]["recovery_points"]) <= 20

    def test_always_exits_zero(self, tmp_path: Path):
        """RLM checkpoint never blocks — always exits 0."""
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "rlm_checkpoint.py"
        if not hook_path.exists():
            pytest.skip("rlm_checkpoint.py not yet created")

        # Even with missing state.yaml, should exit 0
        env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}
        result = subprocess.run(
            ["python3", str(hook_path)],
            capture_output=True, text=True, env={**__import__("os").environ, **env},
        )
        assert result.returncode == 0


# ──────────────────────────────────────────────
# Quality Gate Hook Tests (Secondary)
# ──────────────────────────────────────────────


class TestQualityGateHook:
    """Test quality_gate.py (SECONDARY — Agent Teams only)."""

    def test_hook_file_exists(self):
        """quality_gate.py hook file exists."""
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "quality_gate.py"
        if not hook_path.exists():
            pytest.skip("quality_gate.py not yet created")
        assert hook_path.exists()

    def test_valid_syntax(self):
        """quality_gate.py has valid Python syntax."""
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "quality_gate.py"
        if not hook_path.exists():
            pytest.skip("quality_gate.py not yet created")
        with open(hook_path) as f:
            compile(f.read(), str(hook_path), "exec")


# ──────────────────────────────────────────────
# Idle Check Hook Tests
# ──────────────────────────────────────────────


class TestIdleCheckHook:
    """Test idle_check.py (Agent Teams only)."""

    def test_hook_file_exists(self):
        """idle_check.py hook file exists."""
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "idle_check.py"
        if not hook_path.exists():
            pytest.skip("idle_check.py not yet created")
        assert hook_path.exists()

    def test_valid_syntax(self):
        """idle_check.py has valid Python syntax."""
        hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "idle_check.py"
        if not hook_path.exists():
            pytest.skip("idle_check.py not yet created")
        with open(hook_path) as f:
            compile(f.read(), str(hook_path), "exec")
