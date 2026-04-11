#!/usr/bin/env python3
"""validate_project_init.py — Deterministic validation for project initialization.

Checks PI1-PI8 to verify that project isolation is correctly set up.

Usage:
  python3 scripts/validate_project_init.py --project-dir .
  python3 scripts/validate_project_init.py --project-dir . --project-id 20260318-최윤식

Exit codes:
  0 — all checks pass
  1 — one or more checks fail

Output: JSON to stdout
  {"valid": true, "checks": {...}, "errors": [], "warnings": []}

100% deterministic. Zero AI calls. Zero network calls.
"""

import argparse
import json
import os
import sys


# ─── Constants (must match init_project.py) ──────────────────────────────────

PROJECTS_SUBDIR = "projects"

REQUIRED_OUTPUT_SUBDIRS = [
    "interviews",
    "story-blueprint",
    "story-bible",
    "style-selection",
    "chapters",
    "chapters-ko",
    "builds",
    "eval-reports",
    "comparisons",
]

SYMLINK_MAP = {
    "outputs": "outputs",
    "review-logs": "review-logs",
}

SOT_RELATIVE = os.path.join(".claude", "state.yaml")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _load_yaml(path: str) -> dict | None:
    """Load YAML file. Returns None on failure."""
    if not os.path.isfile(path):
        return None
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None


def _detect_active_project_from_symlink(project_dir: str) -> str | None:
    """Read the outputs symlink to detect active project ID."""
    outputs_path = os.path.join(project_dir, "outputs")
    if not os.path.islink(outputs_path):
        return None
    target = os.readlink(outputs_path)
    # Expected: "projects/{id}/outputs"
    parts = target.split(os.sep)
    if len(parts) >= 2 and parts[0] == PROJECTS_SUBDIR:
        return parts[1]
    return None


# ─── Validation Checks ──────────────────────────────────────────────────────

def validate_project_init(project_dir: str, project_id: str | None = None) -> dict:
    """Run all PI1-PI8 checks.

    Args:
        project_dir: Path to autobiography-generator/ directory.
        project_id: Optional project ID to validate. If None, auto-detected from symlink.

    Returns:
        Structured result dict.
    """
    project_dir = os.path.abspath(project_dir)
    repo_root = os.path.dirname(project_dir)
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, dict] = {}

    # Auto-detect project ID from symlink if not provided
    if project_id is None:
        project_id = _detect_active_project_from_symlink(project_dir)
        if project_id is None:
            checks["PI0"] = {
                "passed": False,
                "detail": "No active project detected — outputs is not a symlink",
            }
            errors.append("PI0: Cannot detect active project. Is outputs a symlink?")
            return {
                "valid": False,
                "checks": checks,
                "errors": errors,
                "warnings": warnings,
            }

    project_path = os.path.join(project_dir, PROJECTS_SUBDIR, project_id)

    # PI1: Project directory exists
    pi1_exists = os.path.isdir(project_path)
    checks["PI1"] = {
        "passed": pi1_exists,
        "detail": f"projects/{project_id}/ {'exists' if pi1_exists else 'NOT FOUND'}",
    }
    if not pi1_exists:
        errors.append(f"PI1: Project directory not found: {project_path}")

    # PI2: All required subdirectories exist
    missing_dirs = []
    for subdir in REQUIRED_OUTPUT_SUBDIRS:
        dir_path = os.path.join(project_path, "outputs", subdir)
        if not os.path.isdir(dir_path):
            missing_dirs.append(subdir)
    # Also check review-logs
    if not os.path.isdir(os.path.join(project_path, "review-logs")):
        missing_dirs.append("review-logs")

    pi2_ok = len(missing_dirs) == 0
    checks["PI2"] = {
        "passed": pi2_ok,
        "detail": (
            f"All {len(REQUIRED_OUTPUT_SUBDIRS) + 1} directories present"
            if pi2_ok
            else f"Missing: {', '.join(missing_dirs)}"
        ),
    }
    if not pi2_ok:
        errors.append(f"PI2: Missing directories: {', '.join(missing_dirs)}")

    # PI3: outputs symlink points to correct project
    outputs_link = os.path.join(project_dir, "outputs")
    pi3_ok = False
    pi3_detail = ""
    if not os.path.islink(outputs_link):
        pi3_detail = "outputs is not a symlink"
        errors.append("PI3: outputs is not a symlink")
    else:
        target = os.readlink(outputs_link)
        expected = os.path.join(PROJECTS_SUBDIR, project_id, "outputs")
        if target == expected:
            pi3_ok = True
            pi3_detail = f"outputs → {target}"
        else:
            pi3_detail = f"outputs → {target} (expected {expected})"
            errors.append(f"PI3: outputs symlink mismatch: {target} != {expected}")
    checks["PI3"] = {"passed": pi3_ok, "detail": pi3_detail}

    # PI4: review-logs symlink points to correct project
    review_link = os.path.join(project_dir, "review-logs")
    pi4_ok = False
    pi4_detail = ""
    if not os.path.islink(review_link):
        pi4_detail = "review-logs is not a symlink"
        errors.append("PI4: review-logs is not a symlink")
    else:
        target = os.readlink(review_link)
        expected = os.path.join(PROJECTS_SUBDIR, project_id, "review-logs")
        if target == expected:
            pi4_ok = True
            pi4_detail = f"review-logs → {target}"
        else:
            pi4_detail = f"review-logs → {target} (expected {expected})"
            errors.append(f"PI4: review-logs symlink mismatch: {target} != {expected}")
    checks["PI4"] = {"passed": pi4_ok, "detail": pi4_detail}

    # PI5: SOT has project.id matching
    sot_path = os.path.join(repo_root, SOT_RELATIVE)
    sot = _load_yaml(sot_path)
    pi5_ok = False
    pi5_detail = ""
    if sot is None:
        pi5_detail = "SOT file not found or invalid"
        warnings.append("PI5: SOT not found — may not be initialized yet")
    else:
        sot_project = sot.get("project", {})
        sot_id = sot_project.get("id", "")
        if sot_id == project_id:
            pi5_ok = True
            pi5_detail = f"SOT project.id = {sot_id}"
        elif not sot_id:
            pi5_detail = "SOT has no project.id field"
            warnings.append("PI5: SOT missing project.id — needs Orchestrator update")
        else:
            pi5_detail = f"SOT project.id = {sot_id} (expected {project_id})"
            errors.append(f"PI5: SOT project.id mismatch: {sot_id} != {project_id}")
    checks["PI5"] = {"passed": pi5_ok, "detail": pi5_detail}

    # PI6: SOT has project.dir matching
    pi6_ok = False
    pi6_detail = ""
    if sot is None:
        pi6_detail = "SOT file not found"
        # Already warned in PI5
    else:
        sot_project = sot.get("project", {})
        sot_dir = sot_project.get("dir", "")
        expected_dir = os.path.join("autobiography-generator", PROJECTS_SUBDIR, project_id)
        if sot_dir == expected_dir:
            pi6_ok = True
            pi6_detail = f"SOT project.dir = {sot_dir}"
        elif not sot_dir:
            pi6_detail = "SOT has no project.dir field"
            warnings.append("PI6: SOT missing project.dir — needs Orchestrator update")
        else:
            pi6_detail = f"SOT project.dir = {sot_dir} (expected {expected_dir})"
            # This might be OK if the path format differs
            warnings.append(f"PI6: SOT project.dir may not match: {sot_dir}")
    checks["PI6"] = {"passed": pi6_ok, "detail": pi6_detail}

    # PI7: Previous project archived if applicable
    projects_base = os.path.join(project_dir, PROJECTS_SUBDIR)
    pi7_ok = True
    pi7_detail = ""
    if os.path.isdir(projects_base):
        project_dirs = [
            d for d in os.listdir(projects_base)
            if os.path.isdir(os.path.join(projects_base, d)) and d != project_id
        ]
        if project_dirs:
            # Check each previous project has a state-snapshot.yaml
            missing_snapshots = []
            for prev_dir in project_dirs:
                snapshot = os.path.join(projects_base, prev_dir, "state-snapshot.yaml")
                if not os.path.isfile(snapshot):
                    missing_snapshots.append(prev_dir)
            if missing_snapshots:
                pi7_ok = False
                pi7_detail = f"Missing state-snapshot.yaml: {', '.join(missing_snapshots)}"
                warnings.append(f"PI7: Previous projects without snapshots: {missing_snapshots}")
            else:
                pi7_detail = f"All {len(project_dirs)} previous project(s) have snapshots"
        else:
            pi7_detail = "No previous projects to archive"
    else:
        pi7_detail = "No projects directory yet"
    checks["PI7"] = {"passed": pi7_ok, "detail": pi7_detail}

    # PI8: No symlink circular references
    pi8_ok = True
    pi8_detail = ""
    for symlink_name in SYMLINK_MAP:
        link_path = os.path.join(project_dir, symlink_name)
        if os.path.islink(link_path):
            # Check for circular reference: does the target exist as a real path?
            resolved = os.path.join(project_dir, os.readlink(link_path))
            if os.path.islink(resolved):
                pi8_ok = False
                pi8_detail = f"Circular: {symlink_name} → symlink → symlink"
                errors.append(f"PI8: Circular symlink detected for {symlink_name}")
                break
            elif not os.path.exists(resolved):
                pi8_ok = False
                pi8_detail = f"Dangling: {symlink_name} → {resolved} (not found)"
                errors.append(f"PI8: Dangling symlink: {symlink_name} → {resolved}")
                break
    if pi8_ok:
        pi8_detail = "No circular or dangling symlinks"
    checks["PI8"] = {"passed": pi8_ok, "detail": pi8_detail}

    # Summary
    valid = len(errors) == 0
    return {
        "valid": valid,
        "project_id": project_id,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate project initialization — PI1-PI8 checks"
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Path to autobiography-generator/ directory",
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="Project ID to validate (auto-detected from symlink if omitted)",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"ERROR: Directory not found: {args.project_dir}", file=sys.stderr)
        sys.exit(1)

    result = validate_project_init(args.project_dir, args.project_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
