#!/usr/bin/env python3
"""
TaskCompleted hook — runs quality gates relevant to the completed task.

Searches for P1 validation scripts in TWO locations:
  1. Project-local scripts/ folder (copied from templates during Phase 3)
  2. Infrastructure hooks/scripts/ folder (always available)

Only runs scripts that exist on disk. Maps task subjects to relevant gates.

Input: JSON on stdin with task metadata
Output: exit 0 (pass or no scripts) or exit 2 + stderr (fail)
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import parse_tool_input, get_project_dir

HOOKS_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Map task subjects to P1 validation scripts
# Scripts are searched in BOTH project/scripts/ AND hooks/scripts/
TASK_GATE_MAP = {
    "skeleton": ["validate_gates.py --gates Q2,Q3,Q5"],
    "content": ["validate_content_insertion.py", "validate_gates.py --gates Q5"],
    "styling": ["validate_design_gates.py"],
    "design": ["validate_design_gates.py"],
    "css": ["validate_design_gates.py"],
    "websocket": ["validate_gates.py --gates Q8,Q9,Q11"],
    "functionality": ["validate_gates.py --gates Q8,Q9,Q11"],
    "pwa": ["validate_gates.py --gates Q3,Q4"],
    "manifest": ["validate_gates.py --gates Q3,Q4"],
    "integration": ["validate_integration.py"],
    "verification": ["validate_integration.py"],
    "deploy": ["validate_gates.py"],
}

# Infrastructure-level scripts (always in hooks/scripts/)
INFRA_SCRIPTS = {
    "validate_app_state_schema.py",
    "validate_content_collection.py",
    "bundle_size_guard.py",
}


def find_script(script_cmd, project_dir):
    """Find a script in project/scripts/ first, then hooks/scripts/.
    Returns (full_path, extra_args) or (None, None)."""
    parts = script_cmd.split(" ", 1)
    script_name = parts[0]
    extra_args = parts[1] if len(parts) > 1 else ""

    # F-9 FIX: Check project-local scripts/ first (Phase 3 copies go here)
    project_scripts = os.path.join(project_dir, "scripts", script_name)
    if os.path.exists(project_scripts):
        return project_scripts, extra_args

    # Then check infrastructure hooks/scripts/
    hooks_scripts = os.path.join(HOOKS_SCRIPTS_DIR, script_name)
    if os.path.exists(hooks_scripts):
        return hooks_scripts, extra_args

    return None, None


def main():
    tool_input = parse_tool_input()
    project_dir = get_project_dir()

    # Determine which gates to run based on task subject
    task_subject = tool_input.get("subject", "").lower()
    scripts_to_run = []

    for keyword, gate_scripts in TASK_GATE_MAP.items():
        if keyword in task_subject:
            scripts_to_run.extend(gate_scripts)
            break

    if not scripts_to_run:
        sys.exit(0)  # No matching gates for this task

    results = []
    any_fail = False

    for script_cmd in scripts_to_run:
        script_path, extra_args = find_script(script_cmd, project_dir)

        if script_path is None:
            results.append({"script": script_cmd, "status": "skipped", "reason": "not found"})
            continue

        cmd = [sys.executable, script_path, "--project-dir", project_dir, "--json"]
        if extra_args:
            cmd.extend(extra_args.split())

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
            )
            if proc.returncode != 0:
                any_fail = True

            # Try to parse JSON output for gate-level results
            try:
                gate_results = json.loads(proc.stdout)
                for gate_id, gate_data in gate_results.items():
                    if isinstance(gate_data, dict) and not gate_data.get("pass", True):
                        print(f"FAIL: {gate_id} — {gate_data.get('detail', 'No detail')}",
                              file=sys.stderr)
                        any_fail = True
            except json.JSONDecodeError:
                pass

            results.append({
                "script": os.path.basename(script_path),
                "status": "passed" if proc.returncode == 0 else "failed",
                "returncode": proc.returncode,
            })
        except subprocess.TimeoutExpired:
            results.append({"script": script_cmd, "status": "timeout"})
            any_fail = True
        except Exception as e:
            results.append({"script": script_cmd, "status": "error", "error": str(e)})

    if any_fail:
        print("Quality gate check found failures. Review and fix before proceeding.",
              file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
