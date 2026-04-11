#!/usr/bin/env python3
"""
Deterministic Phase Error Extraction — H-CRITICAL (Hallucination Prevention)

Reads SOT (app-state.json) and extracts failed quality gates deterministically.
Same SOT input → same output, EVERY TIME. Zero AI judgment.

Usage:
  python3 extract_phase_errors.py --sot-path app-state.json --json
  python3 extract_phase_errors.py --sot-path /path/to/app-state.json

Output (JSON to stdout):
  {
    "failed_gates": [{"id": "Q2", "detail": "...", "source": "q_gates"}, ...],
    "passed_gates": ["Q1", "Q3", ...],
    "retry_count": 3,
    "fallback_tier": 1,
    "has_errors": true,
    "summary": "Failed gates: [Q2, D4]. Retry count: 3. Fallback tier: 1. Details: Q2: HTML invalid; D4: No dark mode"
  }

Exit codes:
  0 — success (JSON output on stdout)
  1 — SOT file not found or invalid JSON
"""

import argparse
import json
import os
import sys


def extract_phase_errors(sot_data):
    """Extract failed quality gates from SOT — DETERMINISTIC.

    Reads from:
      - quality.q_gates        → Q1-Q11 technical gate results
      - quality.d_gates        → D1-D9 design gate results
      - quality.app_specific_gates → app-type-specific gates
      - quality.verify_log     → chronological verification history
      - quality.retry_count    → total retry attempts
      - status.fallback_tier   → current fallback level
    """
    if not sot_data or not isinstance(sot_data, dict):
        return {
            "failed_gates": [], "passed_gates": [],
            "retry_count": 0, "fallback_tier": 1,
            "has_errors": False, "summary": "No SOT data available."
        }

    quality = sot_data.get("quality", {})
    status = sot_data.get("status", {})

    failed = []
    passed = []

    # Scan all gate sources
    for gate_source_name in ("q_gates", "d_gates", "app_specific_gates"):
        gates = quality.get(gate_source_name, {})
        if not isinstance(gates, dict):
            continue
        for gate_id, gate_result in gates.items():
            if isinstance(gate_result, dict):
                gate_status = gate_result.get("status", "").upper()
                if gate_status == "FAIL":
                    failed.append({
                        "id": gate_id,
                        "detail": gate_result.get("detail", ""),
                        "source": gate_source_name,
                    })
                elif gate_status == "PASS":
                    passed.append(gate_id)
            elif isinstance(gate_result, str):
                if gate_result.upper() == "FAIL":
                    failed.append({
                        "id": gate_id, "detail": "",
                        "source": gate_source_name
                    })
                elif gate_result.upper() == "PASS":
                    passed.append(gate_id)

    # Scan verify_log for additional failures
    verify_log = quality.get("verify_log", [])
    if isinstance(verify_log, list):
        for entry in verify_log:
            if isinstance(entry, dict) and entry.get("status", "").upper() == "FAIL":
                gate_id = entry.get("gate_id", entry.get("id", "unknown"))
                if not any(f["id"] == gate_id for f in failed):
                    failed.append({
                        "id": gate_id,
                        "detail": entry.get("detail", entry.get("message", "")),
                        "source": "verify_log",
                    })

    retry_count = quality.get("retry_count", 0)
    if not isinstance(retry_count, int):
        retry_count = 0
    fallback_tier = status.get("fallback_tier", 1)
    if not isinstance(fallback_tier, int):
        fallback_tier = 1
    has_errors = len(failed) > 0 or retry_count > 0

    # Build deterministic summary
    if not has_errors:
        summary = "No errors detected. All gates passed."
    else:
        failed_ids = ", ".join(f["id"] for f in failed)
        details = "; ".join(
            f'{f["id"]}: {f["detail"]}' for f in failed if f["detail"]
        )
        summary = (
            f"Failed gates: [{failed_ids}]. "
            f"Retry count: {retry_count}. "
            f"Fallback tier: {fallback_tier}."
        )
        if details:
            summary += f" Details: {details}"

    return {
        "failed_gates": failed,
        "passed_gates": sorted(passed),
        "retry_count": retry_count,
        "fallback_tier": fallback_tier,
        "has_errors": has_errors,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic Phase Error Extraction (H-CRITICAL)"
    )
    parser.add_argument(
        "--sot-path", required=True,
        help="Path to app-state.json"
    )
    parser.add_argument(
        "--json", action="store_true", default=True,
        help="Output as JSON (default)"
    )
    args = parser.parse_args()

    sot_path = args.sot_path
    if not os.path.exists(sot_path):
        print(json.dumps({
            "error": f"SOT file not found: {sot_path}",
            "failed_gates": [], "passed_gates": [],
            "retry_count": 0, "fallback_tier": 1,
            "has_errors": False, "summary": "SOT file not found."
        }))
        sys.exit(1)

    try:
        with open(sot_path, "r", encoding="utf-8") as f:
            sot_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(json.dumps({
            "error": f"Failed to parse SOT: {e}",
            "failed_gates": [], "passed_gates": [],
            "retry_count": 0, "fallback_tier": 1,
            "has_errors": False, "summary": f"SOT parse error: {e}"
        }))
        sys.exit(1)

    result = extract_phase_errors(sot_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
