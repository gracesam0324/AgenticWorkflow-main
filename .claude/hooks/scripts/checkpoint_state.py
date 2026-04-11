#!/usr/bin/env python3
"""
Stop Hook — State Checkpoint

Triggered on every Stop event to preserve current workflow state.
Creates a timestamped checkpoint in .claude/checkpoints/ for recovery.

Exit codes:
    0 — always
"""

import json
import os
import shutil
import sys
from datetime import datetime


def main():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    state_path = os.path.join(project_dir, ".claude", "state.yaml")
    if not os.path.isfile(state_path):
        sys.exit(0)

    # Create checkpoint directory
    checkpoint_dir = os.path.join(project_dir, ".claude", "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Copy state file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_path = os.path.join(checkpoint_dir, f"state_{timestamp}.yaml")

    try:
        shutil.copy2(state_path, checkpoint_path)
    except OSError as e:
        print(f"WARNING: Could not create checkpoint: {e}", file=sys.stderr)
        sys.exit(0)

    # Rotate old checkpoints (keep last 10)
    checkpoints = sorted(
        [f for f in os.listdir(checkpoint_dir) if f.startswith("state_") and f.endswith(".yaml")],
        reverse=True,
    )
    for old in checkpoints[10:]:
        try:
            os.remove(os.path.join(checkpoint_dir, old))
        except OSError:
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
