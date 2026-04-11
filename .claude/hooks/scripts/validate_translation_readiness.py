#!/usr/bin/env python3
"""
Translation BLOCKING Gate — H-CRITICAL deterministic validator.

Verifies that Phase 1 translation pACS score >= 70 (GREEN) before
allowing transition to Phase 2. AI orchestrator MUST call this
and MUST NOT proceed to Phase 2 if result is {"ready": false}.

This eliminates the hallucination risk where an AI orchestrator
judges "68 is close enough to 70" and proceeds anyway.

Usage: python3 validate_translation_readiness.py --phase <N> [--project-dir <dir>]
Output: JSON {"ready": bool, "phase": N, "score": int, "threshold": 70,
              "color": "GREEN|YELLOW|RED", "detail": "..."}
Exit: 0 = ready (score >= 70), 1 = not ready

Also validates post-Phase 6 batch translation readiness (all phases translated).
"""

import json
import os
import sys
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import read_sot, get_project_dir

THRESHOLD = 70


def extract_pacs_from_log(log_path):
    """Extract pACS score from a translation pACS log file.
    Searches for patterns like: pACS = 75, Translation pACS: 82, Score: 90"""
    if not os.path.exists(log_path):
        return None

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, OSError):
        return None

    # Try multiple patterns
    patterns = [
        r'pACS\s*[=:]\s*(\d+)',
        r'Translation\s+pACS\s*[=:]\s*(\d+)',
        r'Score\s*[=:]\s*(\d+)',
        r'min\(Ft,\s*Ct,\s*Nt\)\s*=\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def extract_pacs_from_sot(phase_num, project_dir=None):
    """Extract translation pACS score from SOT."""
    sot = read_sot(project_dir)
    if not sot:
        return None

    phases = sot.get("translation", {}).get("phases", {})
    phase_data = phases.get(str(phase_num), {})
    return phase_data.get("pacs_score", None)


def check_phase1_blocking(project_dir):
    """Check if Phase 1 translation is GREEN (>= 70).
    This is the BLOCKING gate before Phase 2 can start."""
    score = None

    # Try SOT first
    score = extract_pacs_from_sot(1, project_dir)

    # Try pacs-logs if SOT doesn't have it
    if score is None:
        log_path = os.path.join(project_dir, "pacs-logs", "phase1-translation-pacs.md")
        score = extract_pacs_from_log(log_path)

    if score is None:
        return {
            "ready": False,
            "phase": 1,
            "score": None,
            "threshold": THRESHOLD,
            "color": "RED",
            "detail": "No Phase 1 translation pACS score found. "
                      "Run @app-translator for Phase 1 report first.",
        }

    color = "GREEN" if score >= 70 else ("YELLOW" if score >= 50 else "RED")
    ready = score >= THRESHOLD

    return {
        "ready": ready,
        "phase": 1,
        "score": score,
        "threshold": THRESHOLD,
        "color": color,
        "detail": f"Phase 1 translation pACS = {score}. "
                  f"{'PASS — proceed to Phase 2.' if ready else f'FAIL — must be >= {THRESHOLD}. Re-translate.'}",
    }


def check_batch_readiness(project_dir):
    """Check if all Phase 2-6 translations are complete (post-deployment batch).
    Non-blocking — informational only."""
    results = {}
    all_ready = True

    for phase in range(1, 7):
        score = extract_pacs_from_sot(phase, project_dir)
        if score is None:
            log_patterns = [
                os.path.join(project_dir, "pacs-logs", f"phase{phase}-translation-pacs.md"),
            ]
            for lp in log_patterns:
                score = extract_pacs_from_log(lp)
                if score is not None:
                    break

        if score is None:
            results[f"phase_{phase}"] = {"score": None, "color": "RED", "status": "missing"}
            all_ready = False
        else:
            color = "GREEN" if score >= 70 else ("YELLOW" if score >= 50 else "RED")
            results[f"phase_{phase}"] = {"score": score, "color": color, "status": "ok" if score >= 70 else "low"}
            if score < THRESHOLD:
                all_ready = False

    return {
        "ready": all_ready,
        "phase": "batch",
        "threshold": THRESHOLD,
        "phases": results,
        "detail": "All phases GREEN" if all_ready else "Some phases below threshold or missing",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Translation Readiness Gate Validator (H-CRITICAL)")
    parser.add_argument("--phase", type=int, required=True,
                        help="Phase to check (1 = BLOCKING gate, 7 = batch readiness)")
    parser.add_argument("--project-dir", default=None, help="Project directory")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    project_dir = args.project_dir or get_project_dir()

    if args.phase == 1:
        result = check_phase1_blocking(project_dir)
    elif args.phase == 7 or args.phase == 0:
        # 7 or 0 = check all phases (batch readiness)
        result = check_batch_readiness(project_dir)
    else:
        # Single phase check
        score = extract_pacs_from_sot(args.phase, project_dir)
        if score is None:
            log_path = os.path.join(project_dir, "pacs-logs",
                                     f"phase{args.phase}-translation-pacs.md")
            score = extract_pacs_from_log(log_path)

        color = "GREEN" if score and score >= 70 else ("YELLOW" if score and score >= 50 else "RED")
        result = {
            "ready": score is not None and score >= THRESHOLD,
            "phase": args.phase,
            "score": score,
            "threshold": THRESHOLD,
            "color": color,
            "detail": f"Phase {args.phase} pACS = {score}" if score else "Score not found",
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()
