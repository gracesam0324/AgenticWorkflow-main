#!/usr/bin/env python3
"""Fallback Path Architecture — 3-tier graceful degradation.

NOT a hook — imported as library by Orchestrator (runs in Orchestrator process).

Tier 1: Agent Team → Tier 2: Sequential Subagents → Tier 3: Orchestrator Direct → Tier 4: Human

Each tier represents a progressively simpler execution strategy:
  Tier 1  Agent Team — full parallel agent team execution (default)
  Tier 2  Sequential Subagents — single-agent sequential fallback
  Tier 3  Orchestrator Direct — Orchestrator handles the step itself
  Tier 4  Human Escalation — manual intervention required

Usage (imported by Orchestrator):
    from scripts.fallback_controller import FallbackController

    fc = FallbackController()
    action = fc.handle_failure(step="7c", agent="chapter-writer", error="context overflow")
    # action.tier == 2, action.action == "retry_sequential", ...
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow import both as `from scripts.fallback_controller import ...` (project root)
# and when run directly as `python3 scripts/fallback_controller.py` (script dir).
_this_dir = Path(__file__).resolve().parent
_project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", str(_this_dir.parent))).resolve()
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))

from scripts.sot_lib import load_state, save_state


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FallbackAction:
    """Describes the action the Orchestrator should take after a failure."""

    tier: int               # 1-4: which fallback tier to attempt
    action: str             # machine-readable action key
    feedback: str           # human-readable explanation for the agent/operator
    diagnostic: str         # detailed diagnostic report


@dataclass
class RetryRecord:
    """Tracks retry attempts for a single step."""

    step: str
    agent: str
    error: str
    tier: int
    timestamp: str


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default max retries per step. Override per-step via STEP_RETRY_OVERRIDES.
DEFAULT_MAX_RETRIES: int = 3

# Steps that need more retries (e.g., chapter 1 is critical for voice calibration).
STEP_RETRY_OVERRIDES: dict[str, int] = {
    "9d-ch01": 5,   # Step 9d = Chapter Quality Gate; Ch.1 gets 5 rounds (voice calibration critical)
    "9d-ch1": 5,
    "chapter-1": 5,
}

# Tier definitions for human-readable messages.
TIER_LABELS: dict[int, str] = {
    1: "Agent Team (parallel)",
    2: "Sequential Subagents (single-agent)",
    3: "Orchestrator Direct (no agents)",
    4: "Human Escalation (manual intervention)",
}


# ---------------------------------------------------------------------------
# FallbackController
# ---------------------------------------------------------------------------

class FallbackController:
    """Manages graceful degradation across the 4-tier fallback path.

    State is persisted in SOT via scripts.sot_lib so that retries survive
    across sessions and compactions.

    Args:
        sot_path: Optional override for the SOT file path (for testing).
    """

    def __init__(self, sot_path: Path | None = None) -> None:
        self._sot_path = sot_path
        self._retry_log: list[RetryRecord] = []
        self._load_retry_history()

    # ── Public API ────────────────────────────────────────────────────────

    def handle_failure(
        self,
        step: str,
        agent: str,
        error: str,
    ) -> FallbackAction:
        """Determine the appropriate fallback action for a step failure.

        Algorithm:
          1. Increment retry count for (step, current_tier).
          2. If retries < max_retries → retry at same tier with feedback.
          3. If retries >= max_retries → escalate to next tier.
          4. If already at Tier 4 → return human escalation.

        Args:
            step: Workflow step identifier (e.g., "7c", "7c-ch01").
            agent: Name of the agent that failed.
            error: Error message / description.

        Returns:
            FallbackAction with tier, action, feedback, and diagnostic.
        """
        current_tier = self._current_tier(step)
        retry_count = self.get_retry_count(step)
        max_retries = self.get_max_retries(step)

        diagnostic = self.generate_diagnostic(step, error)

        if current_tier >= 4:
            # Already at human escalation — cannot degrade further.
            action = FallbackAction(
                tier=4,
                action="human_escalation",
                feedback=(
                    f"Step '{step}' has exhausted all automated fallback tiers. "
                    f"Human intervention required.\n\nDiagnostic:\n{diagnostic}"
                ),
                diagnostic=diagnostic,
            )
            self.log_escalation(step, agent, error, tier=4)
            return action

        if retry_count < max_retries:
            # Retry at current tier.
            self.log_retry(step, agent, error, tier=current_tier)
            action = FallbackAction(
                tier=current_tier,
                action="retry_same_tier",
                feedback=(
                    f"Retrying step '{step}' at {TIER_LABELS.get(current_tier, 'unknown')} "
                    f"(attempt {retry_count + 1}/{max_retries}). "
                    f"Error: {error}"
                ),
                diagnostic=diagnostic,
            )
            return action

        # Escalate to next tier.
        next_tier = current_tier + 1
        self.log_degradation(step, agent, error, from_tier=current_tier, to_tier=next_tier)
        self._reset_retry_count(step, next_tier)

        if next_tier == 2:
            action_key = "retry_sequential"
            feedback = (
                f"Step '{step}' failed {max_retries} times at Tier 1 (Agent Team). "
                f"Degrading to Tier 2: Sequential Subagents."
            )
        elif next_tier == 3:
            action_key = "orchestrator_direct"
            feedback = (
                f"Step '{step}' failed at Tier 2 (Sequential Subagents). "
                f"Degrading to Tier 3: Orchestrator Direct execution."
            )
        else:
            action_key = "human_escalation"
            feedback = (
                f"Step '{step}' failed at all automated tiers. "
                f"Escalating to Tier 4: Human intervention."
            )

        return FallbackAction(
            tier=next_tier,
            action=action_key,
            feedback=feedback + f"\n\nDiagnostic:\n{diagnostic}",
            diagnostic=diagnostic,
        )

    def get_retry_count(self, step: str) -> int:
        """Return number of retries so far for the given step at its current tier.

        Args:
            step: Workflow step identifier.

        Returns:
            Number of retry attempts recorded.
        """
        current_tier = self._current_tier(step)
        return sum(
            1 for r in self._retry_log
            if r.step == step and r.tier == current_tier
        )

    def get_max_retries(self, step: str) -> int:
        """Return the maximum retry count allowed for a step.

        Checks STEP_RETRY_OVERRIDES first, then falls back to DEFAULT_MAX_RETRIES.

        Args:
            step: Workflow step identifier.

        Returns:
            Maximum number of retries.
        """
        return STEP_RETRY_OVERRIDES.get(step, DEFAULT_MAX_RETRIES)

    def log_retry(
        self,
        step: str,
        agent: str,
        error: str,
        tier: int,
    ) -> None:
        """Record a retry attempt in the retry log and persist to SOT.

        Args:
            step: Workflow step identifier.
            agent: Name of the agent being retried.
            error: Error that triggered the retry.
            tier: Current fallback tier.
        """
        record = RetryRecord(
            step=step,
            agent=agent,
            error=error,
            tier=tier,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._retry_log.append(record)
        self._persist_state(step, tier, event="retry")

    def log_degradation(
        self,
        step: str,
        agent: str,
        error: str,
        from_tier: int,
        to_tier: int,
    ) -> None:
        """Record a tier degradation event and persist to SOT.

        Args:
            step: Workflow step identifier.
            agent: Name of the agent that exhausted retries.
            error: Error that triggered the degradation.
            from_tier: Tier being abandoned.
            to_tier: Tier being entered.
        """
        record = RetryRecord(
            step=step,
            agent=agent,
            error=f"DEGRADATION {from_tier}->{to_tier}: {error}",
            tier=to_tier,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._retry_log.append(record)
        self._persist_state(step, to_tier, event="degradation")

    def log_escalation(
        self,
        step: str,
        agent: str,
        error: str,
        tier: int,
    ) -> None:
        """Record a human escalation event and persist to SOT.

        Args:
            step: Workflow step identifier.
            agent: Name of the agent involved.
            error: Error that triggered escalation.
            tier: Final tier (should be 4).
        """
        record = RetryRecord(
            step=step,
            agent=agent,
            error=f"HUMAN_ESCALATION: {error}",
            tier=tier,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._retry_log.append(record)
        self._persist_state(step, tier, event="escalation")

    def generate_diagnostic(self, step: str, error: str) -> str:
        """Generate a human-readable diagnostic report for a step failure.

        Args:
            step: Workflow step identifier.
            error: Error message / description.

        Returns:
            Multi-line diagnostic string suitable for operator review.
        """
        current_tier = self._current_tier(step)
        retry_count = self.get_retry_count(step)
        max_retries = self.get_max_retries(step)

        # Gather recent errors for this step.
        step_history = [r for r in self._retry_log if r.step == step]
        recent_errors = step_history[-5:] if step_history else []

        lines = [
            "=" * 60,
            f"FALLBACK DIAGNOSTIC REPORT — Step: {step}",
            "=" * 60,
            f"Current Tier:   {current_tier} ({TIER_LABELS.get(current_tier, 'unknown')})",
            f"Retry Count:    {retry_count} / {max_retries}",
            f"Latest Error:   {error}",
            "",
            "--- Recent Error History ---",
        ]

        if recent_errors:
            for r in recent_errors:
                lines.append(
                    f"  [{r.timestamp}] Tier {r.tier} | {r.agent}: {r.error}"
                )
        else:
            lines.append("  (no prior errors recorded)")

        lines.extend([
            "",
            "--- Recommended Action ---",
        ])

        if retry_count < max_retries:
            lines.append(
                f"  Retry at Tier {current_tier}. "
                f"{max_retries - retry_count} attempt(s) remaining."
            )
        elif current_tier < 4:
            lines.append(
                f"  Escalate to Tier {current_tier + 1} "
                f"({TIER_LABELS.get(current_tier + 1, 'unknown')})."
            )
        else:
            lines.append("  Human intervention required. All tiers exhausted.")

        lines.append("=" * 60)
        return "\n".join(lines)

    # ── Private helpers ───────────────────────────────────────────────────

    def _current_tier(self, step: str) -> int:
        """Determine the current fallback tier for a step from persisted state."""
        try:
            state = load_state(self._sot_path)
        except (FileNotFoundError, OSError):
            return 1

        fallback_data = (
            state.get("orchestration", {})
            .get("fallback", {})
            .get(step, {})
        )
        return fallback_data.get("current_tier", 1)

    def _reset_retry_count(self, step: str, new_tier: int) -> None:
        """Clear retry records for a step when entering a new tier."""
        self._retry_log = [
            r for r in self._retry_log
            if not (r.step == step and r.tier < new_tier)
        ]

    def _load_retry_history(self) -> None:
        """Load retry history from SOT on initialization."""
        try:
            state = load_state(self._sot_path)
        except (FileNotFoundError, OSError):
            return

        fallback_section = state.get("orchestration", {}).get("fallback", {})
        # Skip non-dict entries (activations list, current_tier int)
        for step_key, step_data in fallback_section.items():
            if not isinstance(step_data, dict):
                continue
            for entry in step_data.get("history", []):
                if not isinstance(entry, dict):
                    continue
                self._retry_log.append(RetryRecord(
                    step=step_key,
                    agent=entry.get("agent", "unknown"),
                    error=entry.get("error", ""),
                    tier=entry.get("tier", 1),
                    timestamp=entry.get("timestamp", ""),
                ))

    def _persist_state(self, step: str, tier: int, event: str) -> None:
        """Write current fallback state to SOT atomically.

        Uses merge_orchestration_section() to prevent logical race
        with rlm_checkpoint.py writing to orchestration.rlm.

        Args:
            step: Workflow step identifier.
            tier: Current fallback tier.
            event: Event type (retry, degradation, escalation).
        """
        from scripts.sot_lib import merge_orchestration_section

        # Build the step-level fallback data
        step_data: dict[str, Any] = {
            "current_tier": tier,
            "last_event": event,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        # Build history entry from latest retry record
        latest = self._retry_log[-1] if self._retry_log else None
        if latest and latest.step == step:
            history_entry = {
                "agent": latest.agent,
                "error": latest.error,
                "tier": latest.tier,
                "timestamp": latest.timestamp,
                "event": event,
            }
            step_data["_append_history"] = history_entry

        # Atomically merge into orchestration.fallback
        # merge_orchestration_section holds file lock for entire cycle
        try:
            current_state = load_state(self._sot_path)
            fallback = current_state.get("orchestration", {}).get("fallback", {})
        except (FileNotFoundError, OSError):
            fallback = {"activations": [], "current_tier": 2}

        # Merge step data into fallback section
        existing_step = fallback.get(step, {"current_tier": 1, "history": []})
        if isinstance(existing_step, dict):
            existing_step["current_tier"] = tier
            existing_step["last_event"] = event
            existing_step["last_updated"] = step_data["last_updated"]
            history = existing_step.setdefault("history", [])
            if "_append_history" in step_data:
                history.append(step_data["_append_history"])
                if len(history) > 20:
                    existing_step["history"] = history[-20:]
        else:
            existing_step = step_data

        fallback[step] = existing_step
        merge_orchestration_section("fallback", fallback, sot_path=self._sot_path)


# ---------------------------------------------------------------------------
# CLI (diagnostic only — not the primary usage)
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for diagnostics. Not the primary usage path."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fallback Controller — diagnostic CLI (primary usage is as library import)"
    )
    parser.add_argument(
        "--step", required=True,
        help="Workflow step identifier (e.g., 7c, 7c-ch01)"
    )
    parser.add_argument(
        "--agent", default="unknown",
        help="Agent name"
    )
    parser.add_argument(
        "--error", default="manual diagnostic",
        help="Error description"
    )
    parser.add_argument(
        "--action", choices=["diagnose", "simulate"],
        default="diagnose",
        help="Action to perform"
    )
    args = parser.parse_args()

    fc = FallbackController()

    if args.action == "diagnose":
        report = fc.generate_diagnostic(args.step, args.error)
        print(report)
    elif args.action == "simulate":
        action = fc.handle_failure(args.step, args.agent, args.error)
        print(f"Tier:       {action.tier}")
        print(f"Action:     {action.action}")
        print(f"Feedback:   {action.feedback}")
        print(f"\nDiagnostic:\n{action.diagnostic}")


if __name__ == "__main__":
    main()
