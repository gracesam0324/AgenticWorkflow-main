"""Tests for FallbackController — 3-tier graceful degradation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.fallback_controller import FallbackController


# ──────────────────────────────────────────────
# FallbackController Tests
# ──────────────────────────────────────────────


class TestFallbackController:
    """Test FallbackController behavior (tier transitions, logging)."""

    @pytest.fixture(autouse=True)
    def setup_state(self, tmp_path: Path, valid_state_v2_data: dict[str, Any]):
        """Create state.yaml for FallbackController tests."""
        self.state_path = tmp_path / ".claude" / "state.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            yaml.dump(valid_state_v2_data, f, allow_unicode=True)
        self.project_dir = tmp_path

    def test_retry_within_tier(self):
        """First failure triggers retry within current tier (tier 1 = default from _current_tier)."""
        fc = FallbackController(self.state_path)
        action = fc.handle_failure("step_4", "story-architect", "timeout")
        # Default tier from state is 1 (no per-step fallback data exists yet)
        assert action.action == "retry_same_tier"
        assert "timeout" in action.feedback

    def test_degrade_after_max_retries(self):
        """Exceeding max retries degrades to next tier."""
        fc = FallbackController(self.state_path)
        # Exhaust retries (default max = 3)
        for _ in range(3):
            fc.handle_failure("step_4", "story-architect", "persistent_error")
        action = fc.handle_failure("step_4", "story-architect", "still_failing")
        # Should degrade from tier 1 → tier 2
        assert action.tier == 2
        assert action.action == "retry_sequential"

    def test_degrade_tier_2_to_3(self):
        """Tier 2 degrades to Tier 3 after max retries."""
        fc = FallbackController(self.state_path)
        # First degradation: tier 1 → tier 2 (3 retries then 4th triggers degrade)
        for _ in range(3):
            fc.handle_failure("step_y", "story-architect", "error")
        action = fc.handle_failure("step_y", "story-architect", "error")
        assert action.tier == 2  # Now at tier 2

        # At tier 2: the 3rd retry triggers degradation to tier 3
        fc.handle_failure("step_y", "story-architect", "error_t2")
        fc.handle_failure("step_y", "story-architect", "error_t2")
        action = fc.handle_failure("step_y", "story-architect", "error_t2")
        assert action.tier == 3
        assert action.action == "orchestrator_direct"

    def test_degrade_tier_3_to_human(self):
        """Tier 3 degrades to Tier 4 (human escalation)."""
        fc = FallbackController(self.state_path)
        # Degradation chain: 1→2→3→4
        for tier_round in range(3):  # 3 tiers to exhaust
            for _ in range(3):
                fc.handle_failure("step_4", "story-architect", f"error_tier_{tier_round}")
            fc.handle_failure("step_4", "story-architect", f"trigger_degrade_{tier_round}")

        # At tier 4 now — next failure stays at tier 4
        action = fc.handle_failure("step_4", "story-architect", "final_error")
        assert action.tier == 4
        assert action.action == "human_escalation"
        assert action.diagnostic  # Must have diagnostic report

    def test_fallback_activations_logged(self):
        """Tier degradation events are logged in state.yaml."""
        fc = FallbackController(self.state_path)
        # Exhaust retries to trigger degradation
        for _ in range(3):
            fc.handle_failure("step_4", "story-architect", "error")
        fc.handle_failure("step_4", "story-architect", "trigger_degrade")

        # Check state was persisted
        state = yaml.safe_load(self.state_path.read_text())
        fallback_data = state.get("orchestration", {}).get("fallback", {})
        assert "step_4" in fallback_data
        assert fallback_data["step_4"]["current_tier"] == 2

    def test_chapter_1_gets_more_retries(self):
        """Chapter 1 step gets 5 retries instead of default 3."""
        fc = FallbackController(self.state_path)
        # Use the exact key that's in STEP_RETRY_OVERRIDES
        max_retries = fc.get_max_retries("7c-ch01")
        assert max_retries == 5

    def test_default_max_retries(self):
        """Non-special steps get default 3 retries."""
        fc = FallbackController(self.state_path)
        max_retries = fc.get_max_retries("step_4")
        assert max_retries == 3

    def test_generate_diagnostic(self):
        """Diagnostic report contains step and error info."""
        fc = FallbackController(self.state_path)
        diagnostic = fc.generate_diagnostic("step_4", "Story Bible validation failed: SB-03")
        assert "step_4" in diagnostic
        assert "SB-03" in diagnostic
        assert "DIAGNOSTIC" in diagnostic

    def test_retry_count_starts_at_zero(self):
        """New step has zero retries."""
        fc = FallbackController(self.state_path)
        assert fc.get_retry_count("new_step") == 0

    def test_retry_count_increments(self):
        """Each failure increments retry count."""
        fc = FallbackController(self.state_path)
        fc.handle_failure("step_4", "agent", "error1")
        assert fc.get_retry_count("step_4") == 1
        fc.handle_failure("step_4", "agent", "error2")
        assert fc.get_retry_count("step_4") == 2
