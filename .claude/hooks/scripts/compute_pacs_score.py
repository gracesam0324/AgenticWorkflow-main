#!/usr/bin/env python3
"""
Deterministic pACS Score Calculator — H-CRITICAL (upgraded from H-MAJOR).

Replaces AI judgment in pACS scoring with fully deterministic computation.
AI orchestrator calls this script and uses the output AS-IS. No inflation possible.

Previous design (H-MAJOR):
  compute_pacs_data.py extracts rates → AI applies "judgment" bounded by ceiling
  Problem: AI can still vary between runs (70 vs 75 for same data)

New design (H-CRITICAL):
  compute_pacs_data.py extracts rates → THIS SCRIPT computes final score
  Score = round(rate * 100) for each dimension. No AI judgment. Same input = same output.

Usage: python3 compute_pacs_score.py --project-dir <dir> [--phase <N>] [--json]
Output: JSON {"F": int, "C": int, "L": int, "score": int, "color": "GREEN|YELLOW|RED",
              "ceilings": {...}, "raw_data": {...}, "deterministic": true}
Exit: 0 = computed, 1 = error

The "deterministic: true" flag signals that NO AI judgment was involved.
Every run with identical project state produces identical scores.
"""

import json
import os
import sys
import subprocess
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import get_project_dir


def run_pacs_data_script(project_dir, phase_num):
    """Run compute_pacs_data.py and return parsed JSON."""
    # Search in project/scripts/ first, then templates
    script_locations = [
        os.path.join(project_dir, "scripts", "compute_pacs_data.py"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "..", "skills", "church-retreat-app",
                     "templates", "scripts", "compute_pacs_data.py"),
    ]

    script_path = None
    for loc in script_locations:
        if os.path.exists(loc):
            script_path = loc
            break

    if not script_path:
        return None, "compute_pacs_data.py not found"

    cmd = [sys.executable, script_path, "--project-dir", project_dir, "--json"]
    if phase_num:
        cmd.extend(["--phase", str(phase_num)])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            return None, f"Script error: {proc.stderr[:200]}"
        return json.loads(proc.stdout), None
    except subprocess.TimeoutExpired:
        return None, "Script timeout (60s)"
    except json.JSONDecodeError:
        return None, f"Invalid JSON output: {proc.stdout[:200]}"
    except Exception as e:
        return None, str(e)


def compute_deterministic_score(pacs_data):
    """Compute pACS score deterministically. No AI judgment.

    Formula:
      F = round(F_data.match_rate * 100)
      C = round(C_data.coverage_rate * 100)
      L = round(L_data.gate_pass_rate * 100)
      score = min(F, C, L)

    This is the CEILING from the original design, now promoted to FINAL score.
    Same input → same output. Every time. No variance.
    """
    f_data = pacs_data.get("F_data", {})
    c_data = pacs_data.get("C_data", {})
    l_data = pacs_data.get("L_data", {})

    # Extract rates with safe defaults
    f_rate = f_data.get("match_rate", 0)
    c_rate = c_data.get("coverage_rate", 0)
    l_rate = l_data.get("gate_pass_rate", 0)

    # Deterministic score: rate * 100, rounded to integer
    f_score = round(f_rate * 100)
    c_score = round(c_rate * 100)
    l_score = round(l_rate * 100)

    # Clamp to 0-100
    f_score = max(0, min(100, f_score))
    c_score = max(0, min(100, c_score))
    l_score = max(0, min(100, l_score))

    # Final score = min of all dimensions (weakest link)
    final_score = min(f_score, c_score, l_score)

    # Color classification
    if final_score >= 70:
        color = "GREEN"
    elif final_score >= 50:
        color = "YELLOW"
    else:
        color = "RED"

    return {
        "F": f_score,
        "C": c_score,
        "L": l_score,
        "score": final_score,
        "color": color,
        "ceilings": {"F": f_score, "C": c_score, "L": l_score},
        "raw_data": pacs_data,
        "deterministic": True,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic pACS Score Calculator (H-CRITICAL)")
    parser.add_argument("--project-dir", default=None, help="Project directory")
    parser.add_argument("--phase", type=int, default=None, help="Phase number")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    project_dir = args.project_dir or get_project_dir()

    # Step 1: Get objective data from compute_pacs_data.py
    pacs_data, error = run_pacs_data_script(project_dir, args.phase)

    if error:
        print(json.dumps({
            "error": error,
            "F": 0, "C": 0, "L": 0, "score": 0, "color": "RED",
            "deterministic": True,
        }, indent=2))
        sys.exit(1)

    # Step 2: Compute deterministic score (NO AI judgment)
    result = compute_deterministic_score(pacs_data)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
