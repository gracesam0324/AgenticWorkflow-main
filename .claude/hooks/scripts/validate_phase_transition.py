#!/usr/bin/env python3
"""
Phase Transition Gate — H-CRITICAL deterministic validator.

Verifies that ALL required SOT fields for Phase N are correctly populated
BEFORE allowing transition to Phase N+1. AI orchestrator MUST call this
and MUST NOT proceed if result is {"ready": false}.

Usage: python3 validate_phase_transition.py --phase <N> [--project-dir <dir>]
Output: JSON {"ready": bool, "from_phase": N, "to_phase": N+1, "missing": [...], "invalid": [...]}
Exit: 0 = ready, 1 = not ready (check missing/invalid fields)

This script eliminates the hallucination risk where an AI orchestrator
declares a phase "complete" without actually populating the required SOT fields.
"""

import json
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import read_sot


# ============================================================================
# Phase completion requirements — deterministic field checks
# Each phase defines: {field_path: validator_function}
# validator returns (ok: bool, reason: str)
# ============================================================================

def _exists_and_nonempty(value):
    if value is None:
        return False, "field is None"
    if isinstance(value, str) and value.strip() == "":
        return False, "field is empty string"
    if isinstance(value, list) and len(value) == 0:
        return False, "field is empty list"
    if isinstance(value, dict) and len(value) == 0:
        return False, "field is empty dict"
    return True, "ok"

def _is_true(value):
    if value is True:
        return True, "ok"
    return False, f"expected true, got {value}"

def _is_int_gt0(value):
    if isinstance(value, int) and value > 0:
        return True, "ok"
    return False, f"expected int > 0, got {value}"

def _is_valid_app_type(value):
    valid = {"quiz", "score", "schedule", "lyrics", "stamps", "qt", "prayer", "photo", "combined"}
    if value in valid:
        return True, "ok"
    return False, f"'{value}' not in valid app types: {valid}"

def _is_valid_palette(value):
    if value in ("A", "B", "C"):
        return True, "ok"
    return False, f"'{value}' not in (A, B, C)"


# Phase 0 → 1: Environment must be verified
PHASE_0_REQUIREMENTS = {
    "status.current_phase": lambda v: (v == 0, f"expected 0, got {v}"),
}

# Phase 1 → 2: Intent + content collected
PHASE_1_REQUIREMENTS = {
    "status.research_complete": _is_true,
    "intent.app_type": _is_valid_app_type,
    "intent.design_palette": _is_valid_palette,
}

# Phase 2 → 3: Architecture planned, project initialized
PHASE_2_REQUIREMENTS = {
    "status.planning_complete": _is_true,
    "status.project_folder": _exists_and_nonempty,
    "architecture.tech_stack": _exists_and_nonempty,
    "architecture.deployment_type": _exists_and_nonempty,
}

# Phase 3 → 4: Code generated
PHASE_3_REQUIREMENTS = {
    "status.code_generated": _is_true,
    "status.last_git_checkpoint": _exists_and_nonempty,
}

# Phase 4 → 5: Quality verified
PHASE_4_REQUIREMENTS = {
    "status.quality_passed": _is_true,
    "quality.pacs_score": lambda v: (isinstance(v, (int, float)) and v >= 50,
                                      f"pACS score {v} < 50 (RED — rework required)"),
}

# Phase 5 → 6: User approved (completion signal confirmed)
PHASE_5_REQUIREMENTS = {
    # No strict field requirement — orchestrator asks "이대로 배포할까요?"
    # and user confirms. We check that preview loop was entered.
    "status.current_phase": lambda v: (v == 5, f"expected 5, got {v}"),
}

# Phase 6 complete: Deployed
PHASE_6_REQUIREMENTS = {
    "status.deployed": _is_true,
    "status.server_url": _exists_and_nonempty,
}

PHASE_REQUIREMENTS = {
    0: PHASE_0_REQUIREMENTS,
    1: PHASE_1_REQUIREMENTS,
    2: PHASE_2_REQUIREMENTS,
    3: PHASE_3_REQUIREMENTS,
    4: PHASE_4_REQUIREMENTS,
    5: PHASE_5_REQUIREMENTS,
    6: PHASE_6_REQUIREMENTS,
}

# App-type-specific Phase 1 requirements (extends PHASE_1_REQUIREMENTS)
APP_TYPE_PHASE1_EXTRAS = {
    "quiz": {
        "intent.team_count": _is_int_gt0,
        "intent.team_names": _exists_and_nonempty,
        "content.quiz_questions": _exists_and_nonempty,
    },
    "score": {
        "intent.team_count": _is_int_gt0,
        "intent.team_names": _exists_and_nonempty,
        "intent.team_colors": _exists_and_nonempty,
    },
    "schedule": {
        "content.schedule": _exists_and_nonempty,
    },
    "lyrics": {
        "content.lyrics": _exists_and_nonempty,
    },
    "stamps": {
        "content.missions": _exists_and_nonempty,
    },
    "qt": {
        "content.bible_passages": _exists_and_nonempty,
    },
    "combined": {
        "intent.features": _exists_and_nonempty,
    },
    # prayer, photo: no extra content required
}


def get_nested(data, field_path):
    """Get nested dict value using dot notation. Returns None if not found."""
    keys = field_path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def validate_phase(phase_num, sot_data):
    """Validate that Phase N is complete and ready for Phase N+1.
    Returns (ready: bool, missing: list, invalid: list)."""
    requirements = PHASE_REQUIREMENTS.get(phase_num, {})
    missing = []
    invalid = []

    # Base requirements for this phase
    for field_path, validator in requirements.items():
        value = get_nested(sot_data, field_path)
        if value is None:
            missing.append(field_path)
            continue
        ok, reason = validator(value)
        if not ok:
            invalid.append({"field": field_path, "value": str(value)[:50], "reason": reason})

    # App-type-specific extras for Phase 1
    if phase_num == 1:
        app_type = get_nested(sot_data, "intent.app_type")
        if app_type and app_type in APP_TYPE_PHASE1_EXTRAS:
            for field_path, validator in APP_TYPE_PHASE1_EXTRAS[app_type].items():
                value = get_nested(sot_data, field_path)
                if value is None:
                    missing.append(field_path)
                    continue
                ok, reason = validator(value)
                if not ok:
                    invalid.append({"field": field_path, "value": str(value)[:50], "reason": reason})

    ready = len(missing) == 0 and len(invalid) == 0
    return ready, missing, invalid


def main():
    parser = argparse.ArgumentParser(description="Phase Transition Gate Validator (H-CRITICAL)")
    parser.add_argument("--phase", type=int, required=True, help="Current phase number (0-6)")
    parser.add_argument("--project-dir", default=None, help="Project directory")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    if args.phase < 0 or args.phase > 6:
        print(json.dumps({"error": f"Invalid phase: {args.phase}. Must be 0-6."}))
        sys.exit(1)

    sot_data = read_sot(args.project_dir)
    if not sot_data:
        print(json.dumps({
            "ready": False,
            "from_phase": args.phase,
            "to_phase": args.phase + 1 if args.phase < 6 else None,
            "missing": ["app-state.json not found or empty"],
            "invalid": [],
        }))
        sys.exit(1)

    ready, missing, invalid = validate_phase(args.phase, sot_data)

    result = {
        "ready": ready,
        "from_phase": args.phase,
        "to_phase": args.phase + 1 if args.phase < 6 else None,
        "missing": missing,
        "invalid": invalid,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
