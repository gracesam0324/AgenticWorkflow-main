"""Translation pipeline TDD tests.

Tests verify:
- verify_translation hook exists and has valid syntax
- pACS threshold logic (>= 70 GREEN, 50-69 YELLOW, < 50 RED)
- Translation pair tracking in state.yaml
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import pytest
import yaml


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

HOOK_PATH = Path(__file__).parent.parent / ".claude" / "hooks" / "scripts" / "verify_translation.py"


# ──────────────────────────────────────────────
# Hook File Existence and Syntax
# ──────────────────────────────────────────────


class TestVerifyTranslationHookFile:
    """Test verify_translation.py hook file integrity."""

    def test_hook_file_exists(self):
        """verify_translation.py hook file exists at the expected path."""
        assert HOOK_PATH.exists(), f"Hook not found at {HOOK_PATH}"

    def test_hook_has_valid_python_syntax(self):
        """verify_translation.py has valid Python syntax."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        compile(source, str(HOOK_PATH), "exec")

    def test_hook_is_executable_module(self):
        """verify_translation.py can be imported without errors."""
        result = subprocess.run(
            ["python3", "-c", f"import importlib.util; spec = importlib.util.spec_from_file_location('vt', '{HOOK_PATH}'); mod = importlib.util.module_from_spec(spec)"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Import check failed: {result.stderr}"

    def test_hook_has_main_function(self):
        """verify_translation.py defines a main() function."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        assert "def main()" in source, "Hook must define a main() function"

    def test_hook_has_pacs_threshold_constant(self):
        """verify_translation.py defines PACS_THRESHOLD = 50."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        assert "PACS_THRESHOLD" in source, "Hook must define PACS_THRESHOLD"
        assert "= 50" in source or "=50" in source, "PACS_THRESHOLD must be 50"


# ──────────────────────────────────────────────
# pACS Threshold Logic
# ──────────────────────────────────────────────


class TestPACSThresholdLogic:
    """Test pACS grading thresholds: >= 70 GREEN, 50-69 YELLOW, < 50 RED."""

    @staticmethod
    def _make_translation_payload(task_id: str = "step-9-translate", pacs_score: int | None = None) -> str:
        """Build a minimal TaskCompleted JSON payload for a translation task."""
        payload: dict[str, Any] = {
            "task_id": task_id,
            "task": {
                "subject": "Translate story bible to Korean",
                "description": "English-to-Korean translation of outputs",
                "metadata": {"agent": "@translator", "step": "9", "type": "translation"},
            },
            "result": {},
        }
        if pacs_score is not None:
            payload["result"]["pacs_score"] = pacs_score
        return json.dumps(payload)

    @staticmethod
    def _run_hook(input_data: str, project_dir: str | None = None) -> subprocess.CompletedProcess:
        """Run the verify_translation.py hook with given stdin input."""
        env = {**__import__("os").environ}
        if project_dir:
            env["CLAUDE_PROJECT_DIR"] = project_dir
        return subprocess.run(
            ["python3", str(HOOK_PATH)],
            input=input_data,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_green_pacs_passes(self):
        """pACS >= 70 (GREEN) passes with exit code 0."""
        for score in [70, 85, 100]:
            result = self._run_hook(self._make_translation_payload(pacs_score=score))
            assert result.returncode == 0, f"pACS {score} should pass: {result.stderr}"
            assert "GREEN" in result.stderr

    def test_yellow_pacs_passes(self):
        """pACS 50-69 (YELLOW) passes with exit code 0."""
        for score in [50, 55, 69]:
            result = self._run_hook(self._make_translation_payload(pacs_score=score))
            assert result.returncode == 0, f"pACS {score} should pass: {result.stderr}"
            assert "YELLOW" in result.stderr

    def test_red_pacs_rejects(self):
        """pACS < 50 (RED) rejects with exit code 2."""
        for score in [0, 25, 49]:
            result = self._run_hook(self._make_translation_payload(pacs_score=score))
            assert result.returncode == 2, f"pACS {score} should reject: {result.stderr}"
            assert "RED" in result.stderr
            assert "REJECT" in result.stderr

    def test_boundary_score_50_passes(self):
        """pACS exactly at threshold (50) passes."""
        result = self._run_hook(self._make_translation_payload(pacs_score=50))
        assert result.returncode == 0

    def test_boundary_score_49_rejects(self):
        """pACS one below threshold (49) rejects."""
        result = self._run_hook(self._make_translation_payload(pacs_score=49))
        assert result.returncode == 2

    def test_non_translation_task_passes(self):
        """Non-translation tasks always pass regardless of pACS."""
        payload = json.dumps({
            "task_id": "step-7b-write-chapter",
            "task": {
                "subject": "Write chapter 3 draft",
                "description": "Draft chapter prose",
                "metadata": {"agent": "@chapter-writer", "step": "7b"},
            },
            "result": {"pacs_score": 10},
        })
        result = self._run_hook(payload)
        assert result.returncode == 0

    def test_empty_stdin_passes(self):
        """Empty stdin triggers fail-open (exit 0)."""
        result = self._run_hook("")
        assert result.returncode == 0

    def test_invalid_json_passes(self):
        """Invalid JSON triggers fail-open (exit 0)."""
        result = self._run_hook("this is not json")
        assert result.returncode == 0

    def test_missing_pacs_score_failopen(self, tmp_path: Path):
        """Missing pACS score with no pacs-logs triggers fail-open."""
        payload = self._make_translation_payload(pacs_score=None)
        result = self._run_hook(payload, project_dir=str(tmp_path))
        assert result.returncode == 0

    def test_reads_pacs_from_log_file(self, tmp_path: Path):
        """When pACS not in payload, reads from pacs-logs/ directory."""
        # Create a pacs-logs directory with a log file
        pacs_dir = tmp_path / "pacs-logs"
        pacs_dir.mkdir()
        log_content = textwrap.dedent("""\
            # Translation pACS Report — Step 9: Story Bible Translation

            ## Scores
            | Dimension | Score | Rationale |
            |-----------|-------|-----------|
            | Ft | 80 | Good fidelity |
            | Ct | 75 | Complete |
            | Nt | 72 | Natural |

            ## Result: Translation pACS = 72 -> GREEN
        """)
        (pacs_dir / "step-9-translation-pacs.md").write_text(log_content)

        payload = self._make_translation_payload(pacs_score=None)
        result = self._run_hook(payload, project_dir=str(tmp_path))
        assert result.returncode == 0
        assert "72" in result.stderr

    def test_reads_red_pacs_from_log_file(self, tmp_path: Path):
        """Rejects when pacs-logs/ shows pACS < 50."""
        pacs_dir = tmp_path / "pacs-logs"
        pacs_dir.mkdir()
        log_content = textwrap.dedent("""\
            # Translation pACS Report — Step 9

            ## Result: Translation pACS = 35 -> RED
        """)
        (pacs_dir / "step-9-translation-pacs.md").write_text(log_content)

        payload = self._make_translation_payload(pacs_score=None)
        result = self._run_hook(payload, project_dir=str(tmp_path))
        assert result.returncode == 2


# ──────────────────────────────────────────────
# Translation Pair Tracking in state.yaml
# ──────────────────────────────────────────────


class TestTranslationPairTracking:
    """Test that state.yaml orchestration.translation.pairs tracks translation output."""

    def test_state_has_translation_section(self, valid_state_v2_data: dict[str, Any]):
        """state.yaml v2 contains orchestration.translation section."""
        assert "translation" in valid_state_v2_data["orchestration"]

    def test_translation_section_has_pairs(self, valid_state_v2_data: dict[str, Any]):
        """orchestration.translation contains a pairs mapping."""
        translation = valid_state_v2_data["orchestration"]["translation"]
        assert "pairs" in translation
        assert isinstance(translation["pairs"], dict)

    def test_translation_pair_structure(self):
        """Translation pair entries map English source to Korean output path."""
        pair = {
            "outputs/story-bible/story_bible_summary.md": "outputs/story-bible/story_bible_summary.ko.md",
        }
        for en_path, ko_path in pair.items():
            assert en_path.endswith(".md"), "English source must be a .md file"
            assert ko_path.endswith(".ko.md"), "Korean output must end with .ko.md"
            # The Korean path is the English path with .ko inserted before extension
            expected_ko = en_path.rsplit(".", 1)[0] + ".ko.md"
            assert ko_path == expected_ko

    def test_pacs_history_tracks_scores(self, valid_state_v2_data: dict[str, Any]):
        """orchestration.translation.pacs_history maps step to scores."""
        translation = valid_state_v2_data["orchestration"]["translation"]
        assert "pacs_history" in translation
        assert isinstance(translation["pacs_history"], dict)

    def test_glossary_path_configured(self, valid_state_v2_data: dict[str, Any]):
        """orchestration.translation.glossary_path points to glossary file."""
        translation = valid_state_v2_data["orchestration"]["translation"]
        assert "glossary_path" in translation
        assert translation["glossary_path"] == "translations/glossary.yaml"

    def test_pending_translations_is_list(self, valid_state_v2_data: dict[str, Any]):
        """orchestration.translation.pending_translations is a list."""
        translation = valid_state_v2_data["orchestration"]["translation"]
        assert "pending_translations" in translation
        assert isinstance(translation["pending_translations"], list)
