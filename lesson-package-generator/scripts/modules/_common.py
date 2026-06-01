"""Shared helpers for pipeline step modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.claude_client import call_claude
from scripts.io_helpers import project_root_from_script, read_prompt


def prompts_dir() -> Path:
    return project_root_from_script() / "agents" / "prompts"


def run_step(
    *,
    step_id: str,
    prompt_filename: str,
    intake: dict[str, Any],
    prior: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Load prompt, call Claude once, return raw text + structured stub payload."""
    system_prompt = read_prompt(prompts_dir() / prompt_filename)
    user_payload: dict[str, Any] = {"intake": intake, **prior}
    raw_text = call_claude(
        step_id=step_id,
        system_prompt=system_prompt,
        user_payload=user_payload,
    )
    structured = {
        "step_id": step_id,
        "status": "placeholder",
        "raw_text": raw_text,
        "intake_ref": {
            "audience": intake.get("audience"),
            "volume": intake.get("volume"),
            "emphasis": intake.get("emphasis"),
        },
        "prior_keys": list(prior.keys()),
    }
    return raw_text, structured
