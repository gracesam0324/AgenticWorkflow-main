#!/usr/bin/env python3
"""
P1 Data Extraction: pACS Objective Data (H-MAJOR).

Extracts OBJECTIVE data for pACS scoring. Does NOT assign scores — AI does that.

- F_data (Content Accuracy): calls validate_content_insertion.py → match_rate
- C_data (Feature Completeness): SOT features → routes/elements check
- L_data (Code Correctness): calls validate_gates.py + validate_design_gates.py → pass rates

Usage:
    python3 compute_pacs_data.py --project-dir . [--json]

Output (JSON):
    {"F_data": {"match_rate": 0.95, ...},
     "C_data": {"coverage_rate": 1.0, ...},
     "L_data": {"gate_pass_rate": 0.87, ...}}

SOT: Read-only.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def read_sot(project_dir):
    """Read app-state.json."""
    sot_path = os.path.join(project_dir, "app-state.json")
    try:
        with open(sot_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, FileNotFoundError):
        return {}


def run_script(script_name, project_dir, extra_args=None):
    """Run a sibling P1 script and return JSON result."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)

    if not os.path.exists(script_path):
        return {"error": f"Script not found: {script_name}"}

    cmd = [sys.executable, script_path, "--project-dir", project_dir, "--json"]
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return {"error": f"Script exited {result.returncode}: {result.stderr[:200]}"}
    except subprocess.TimeoutExpired:
        return {"error": f"Script timed out: {script_name}"}
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON from {script_name}"}
    except Exception as e:
        return {"error": f"Failed to run {script_name}: {e}"}


def read_files(project_dir, ext):
    """Read all files of given extension."""
    content = ""
    for root, _dirs, files in os.walk(project_dir):
        if any(skip in root for skip in ["node_modules", ".git", "scripts"]):
            continue
        for f in files:
            if f.endswith(ext):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                        content += fh.read() + "\n"
                except (UnicodeDecodeError, OSError):
                    pass
    return content


def compute_f_data(project_dir):
    """F_data: Content Accuracy — from validate_content_insertion.py."""
    result = run_script("validate_content_insertion.py", project_dir)

    if "error" in result:
        return {"match_rate": 0, "missing_items": [], "error": result["error"]}

    return {
        "match_rate": result.get("match_rate", 0),
        "total_in_sot": result.get("total_in_sot", 0),
        "found_in_html": result.get("found_in_html", 0),
        "missing_items": [m.get("text", "")[:50] for m in result.get("missing", [])],
    }


def compute_c_data(project_dir):
    """C_data: Feature Completeness — SOT features vs implemented routes/elements."""
    sot = read_sot(project_dir)
    intent = sot.get("intent", {})
    app_type = intent.get("app_type", "")
    features = intent.get("features", [])

    # For non-combined apps, derive expected features from app type
    if not features:
        FEATURE_MAP = {
            "quiz": ["quiz_page", "admin", "screen", "websocket"],
            "score": ["score_page", "admin", "screen", "websocket"],
            "lyrics": ["lyrics_page", "admin", "screen", "websocket"],
            "schedule": ["schedule_page"],
            "qt": ["qt_page"],
            "stamps": ["stamps_page", "admin", "qr_missions"],
            "photo": ["gallery_page", "admin"],
            "prayer": ["prayer_page"],
            "combined": [],
        }
        features = FEATURE_MAP.get(app_type, [])

    if not features:
        return {"coverage_rate": 1.0, "implemented": [], "unimplemented": [],
                "detail": "No features to check"}

    # Check implementation by searching for routes and HTML elements
    js = read_files(project_dir, ".js")
    html = read_files(project_dir, ".html")
    combined = js + html

    implemented = []
    unimplemented = []

    for feature in features:
        # Normalize feature name for search
        search_terms = [feature.lower().replace("_", ""),
                        feature.lower().replace("_", "-"),
                        feature.lower()]

        found = any(term in combined.lower() for term in search_terms)
        if found:
            implemented.append(feature)
        else:
            unimplemented.append(feature)

    total = len(features)
    coverage = len(implemented) / total if total > 0 else 1.0

    return {
        "coverage_rate": round(coverage, 4),
        "total_features": total,
        "implemented": implemented,
        "unimplemented": unimplemented,
    }


def compute_l_data(project_dir):
    """L_data: Code Correctness — gate pass rates from validate_gates + validate_design_gates."""
    sot = read_sot(project_dir)
    app_type = sot.get("intent", {}).get("app_type", "quiz")

    q_results = run_script("validate_gates.py", project_dir)
    d_results = run_script("validate_design_gates.py", project_dir)

    passing = []
    failing = []

    for gate_id, result in {**q_results, **d_results}.items():
        if isinstance(result, dict) and "pass" in result:
            if result["pass"]:
                passing.append(gate_id)
            else:
                failing.append(gate_id)

    total = len(passing) + len(failing)
    rate = len(passing) / total if total > 0 else 0

    return {
        "gate_pass_rate": round(rate, 4),
        "total_gates": total,
        "passing": sorted(passing),
        "failing": sorted(failing),
    }


def main():
    parser = argparse.ArgumentParser(description="Extract objective pACS data (H-MAJOR)")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"Directory not found: {project_dir}"}))
        sys.exit(1)

    results = {
        "F_data": compute_f_data(project_dir),
        "C_data": compute_c_data(project_dir),
        "L_data": compute_l_data(project_dir),
    }

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("=== pACS Objective Data ===")
        print(f"\nF_data (Content Accuracy):")
        print(f"  Match rate: {results['F_data'].get('match_rate', 'N/A')}")
        print(f"  Missing: {results['F_data'].get('missing_items', [])}")
        print(f"\nC_data (Feature Completeness):")
        print(f"  Coverage: {results['C_data'].get('coverage_rate', 'N/A')}")
        print(f"  Unimplemented: {results['C_data'].get('unimplemented', [])}")
        print(f"\nL_data (Code Correctness):")
        print(f"  Gate pass rate: {results['L_data'].get('gate_pass_rate', 'N/A')}")
        print(f"  Failing: {results['L_data'].get('failing', [])}")


if __name__ == "__main__":
    main()
