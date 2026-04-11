#!/usr/bin/env python3
"""
Continuous Quality Dashboard for AI Autobiography Generator.

Reads all evaluation logs, shows quality trends over time, highlights
regressions, and outputs a markdown report.

Usage:
    python3 dashboard.py                        # Full report to stdout
    python3 dashboard.py --output report.md     # Save markdown report
    python3 dashboard.py --json                 # Machine-readable output
    python3 dashboard.py --last 10              # Only last N evaluations
    python3 dashboard.py --dimension emotional_authenticity  # Single dimension focus
    python3 dashboard.py --alert-threshold 0.75  # Custom alert threshold
"""

import json
import os
import sys
import argparse
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_LOGS_DIR = SCRIPT_DIR / ".eval-logs"
JUDGE_SCORES_PATH = EVAL_LOGS_DIR / "judge_scores.jsonl"
BASELINE_DIR = SCRIPT_DIR / ".quality-baselines"

DIMENSIONS = [
    "emotional_authenticity",
    "sensory_detail_preservation",
    "narrative_flow",
    "voice_consistency",
    "factual_grounding",
]

# Severity thresholds
DEFAULT_ALERT_THRESHOLD = 0.75
DEFAULT_CRITICAL_THRESHOLD = 0.60
DEFAULT_REGRESSION_DELTA = -0.05


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_eval_logs() -> list[dict]:
    """Load all evaluation run logs (JSON files in .eval-logs/)."""
    if not EVAL_LOGS_DIR.exists():
        return []

    entries = []
    for f in sorted(EVAL_LOGS_DIR.glob("eval_*.json")):
        try:
            data = json.loads(f.read_text())
            data["_source_file"] = f.name
            entries.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return entries


def load_judge_scores() -> list[dict]:
    """Load individual judge score entries (JSONL format)."""
    if not JUDGE_SCORES_PATH.exists():
        return []

    entries = []
    with open(JUDGE_SCORES_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def load_latest_baseline() -> Optional[dict]:
    """Load the most recent quality baseline."""
    latest = BASELINE_DIR / "baseline_latest.json"
    if latest.exists():
        try:
            return json.loads(latest.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return None


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def compute_trends(entries: list[dict], window: int = 5) -> dict:
    """
    Compute quality trends from evaluation log entries.
    Uses a sliding window to smooth noise from non-deterministic scoring.
    """
    if not entries:
        return {"error": "No evaluation data available"}

    # Collect scores per dimension over time
    dimension_series = defaultdict(list)
    test_series = defaultdict(lambda: defaultdict(list))
    timestamps = []

    for entry in entries:
        ts = entry.get("timestamp", "")
        timestamps.append(ts)
        results = entry.get("results", {})
        for test_id, result in results.items():
            scores = result.get("llm_scores", {})
            for dim, score in scores.items():
                dimension_series[dim].append({"ts": ts, "score": score, "test_id": test_id})
                test_series[test_id][dim].append({"ts": ts, "score": score})

    trends = {}
    for dim in DIMENSIONS:
        series = dimension_series.get(dim, [])
        if not series:
            trends[dim] = {"status": "no_data"}
            continue

        all_scores = [s["score"] for s in series]
        n = len(all_scores)

        current = {
            "latest": all_scores[-1] if all_scores else 0,
            "mean": round(statistics.mean(all_scores), 4),
            "median": round(statistics.median(all_scores), 4),
            "stdev": round(statistics.stdev(all_scores), 4) if n > 1 else 0,
            "min": round(min(all_scores), 4),
            "max": round(max(all_scores), 4),
            "count": n,
        }

        # Trend: compare recent window to overall mean
        if n >= window:
            recent = all_scores[-window:]
            older = all_scores[:-window]
            recent_mean = statistics.mean(recent)
            older_mean = statistics.mean(older) if older else recent_mean
            delta = recent_mean - older_mean

            if delta > 0.03:
                trend_label = "improving"
            elif delta < -0.03:
                trend_label = "declining"
            else:
                trend_label = "stable"

            current["trend"] = trend_label
            current["trend_delta"] = round(delta, 4)
            current["recent_mean"] = round(recent_mean, 4)
        else:
            current["trend"] = "insufficient_data"
            current["trend_delta"] = 0

        trends[dim] = current

    return {
        "dimensions": trends,
        "total_evaluations": len(entries),
        "date_range": {
            "first": timestamps[0] if timestamps else None,
            "last": timestamps[-1] if timestamps else None,
        },
    }


def detect_regressions(
    entries: list[dict],
    baseline: Optional[dict],
    alert_threshold: float = DEFAULT_ALERT_THRESHOLD,
    regression_delta: float = DEFAULT_REGRESSION_DELTA,
) -> list[dict]:
    """
    Detect quality regressions by comparing latest results to baseline
    and to historical averages.
    """
    regressions = []

    if not entries:
        return regressions

    latest_entry = entries[-1]
    latest_results = latest_entry.get("results", {})

    # Compare to baseline
    if baseline:
        baseline_results = baseline.get("results", {})
        for test_id, latest_result in latest_results.items():
            if test_id not in baseline_results:
                continue
            baseline_result = baseline_results[test_id]
            latest_scores = latest_result.get("llm_scores", {})
            baseline_scores = baseline_result.get("llm_scores", {})

            for dim in DIMENSIONS:
                curr = latest_scores.get(dim, 0)
                base = baseline_scores.get(dim, 0)
                delta = curr - base
                if delta <= regression_delta:
                    regressions.append({
                        "type": "baseline_regression",
                        "test_id": test_id,
                        "dimension": dim,
                        "baseline_score": round(base, 4),
                        "current_score": round(curr, 4),
                        "delta": round(delta, 4),
                        "severity": "critical" if delta <= regression_delta * 2 else "warning",
                    })

    # Compare to historical average
    if len(entries) >= 3:
        historical = entries[:-1]  # All except latest
        hist_scores = defaultdict(lambda: defaultdict(list))
        for entry in historical:
            for test_id, result in entry.get("results", {}).items():
                for dim, score in result.get("llm_scores", {}).items():
                    hist_scores[test_id][dim].append(score)

        for test_id, latest_result in latest_results.items():
            latest_scores = latest_result.get("llm_scores", {})
            for dim in DIMENSIONS:
                curr = latest_scores.get(dim, 0)
                hist_list = hist_scores.get(test_id, {}).get(dim, [])
                if hist_list:
                    hist_mean = statistics.mean(hist_list)
                    delta = curr - hist_mean
                    if delta <= regression_delta and curr < alert_threshold:
                        regressions.append({
                            "type": "historical_regression",
                            "test_id": test_id,
                            "dimension": dim,
                            "historical_mean": round(hist_mean, 4),
                            "current_score": round(curr, 4),
                            "delta": round(delta, 4),
                            "severity": "critical" if curr < DEFAULT_CRITICAL_THRESHOLD else "warning",
                        })

    # Check absolute threshold violations
    for test_id, latest_result in latest_results.items():
        latest_scores = latest_result.get("llm_scores", {})
        for dim in DIMENSIONS:
            score = latest_scores.get(dim, 0)
            if score < DEFAULT_CRITICAL_THRESHOLD:
                regressions.append({
                    "type": "threshold_violation",
                    "test_id": test_id,
                    "dimension": dim,
                    "threshold": DEFAULT_CRITICAL_THRESHOLD,
                    "current_score": round(score, 4),
                    "severity": "critical",
                })

    return regressions


def compute_test_reliability(entries: list[dict]) -> dict:
    """
    Analyze scoring consistency across evaluations.
    High stdev in scores suggests either quality instability or judge noise.
    """
    reliability = {}
    dim_scores = defaultdict(lambda: defaultdict(list))

    for entry in entries:
        for test_id, result in entry.get("results", {}).items():
            for dim, score in result.get("llm_scores", {}).items():
                dim_scores[test_id][dim].append(score)

    for test_id, dims in dim_scores.items():
        test_rel = {}
        for dim, scores in dims.items():
            if len(scores) > 1:
                test_rel[dim] = {
                    "mean": round(statistics.mean(scores), 4),
                    "stdev": round(statistics.stdev(scores), 4),
                    "cv": round(statistics.stdev(scores) / max(statistics.mean(scores), 0.01), 4),
                    "range": round(max(scores) - min(scores), 4),
                    "n": len(scores),
                    "reliable": statistics.stdev(scores) < 0.10,
                }
            else:
                test_rel[dim] = {"mean": scores[0] if scores else 0, "n": 1, "reliable": None}
        reliability[test_id] = test_rel

    return reliability


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_sparkline(values: list[float], width: int = 20) -> str:
    """Generate a text-based sparkline from a series of values."""
    if not values:
        return " " * width
    chars = " _.,:-=!#"
    min_v = min(values)
    max_v = max(values)
    range_v = max_v - min_v if max_v > min_v else 1

    # Sample or pad to fit width
    if len(values) > width:
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values + [values[-1]] * (width - len(values))

    line = ""
    for v in sampled:
        idx = int((v - min_v) / range_v * (len(chars) - 1))
        line += chars[min(idx, len(chars) - 1)]
    return line


def generate_markdown_report(
    trends: dict,
    regressions: list[dict],
    reliability: dict,
    entries: list[dict],
    alert_threshold: float,
) -> str:
    """Generate a comprehensive markdown quality dashboard report."""
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append("# Quality Dashboard Report")
    lines.append(f"Generated: {now}")
    lines.append("")

    # Overview
    total_evals = trends.get("total_evaluations", 0)
    date_range = trends.get("date_range", {})
    lines.append("## Overview")
    lines.append(f"- Total evaluations: **{total_evals}**")
    if date_range.get("first"):
        lines.append(f"- Date range: {date_range['first'][:10]} to {date_range['last'][:10]}")
    lines.append(f"- Alert threshold: {alert_threshold}")
    lines.append(f"- Critical threshold: {DEFAULT_CRITICAL_THRESHOLD}")
    lines.append("")

    # Regression Alerts
    if regressions:
        critical = [r for r in regressions if r["severity"] == "critical"]
        warnings = [r for r in regressions if r["severity"] == "warning"]

        lines.append("## Alerts")
        lines.append("")
        if critical:
            lines.append(f"### CRITICAL ({len(critical)})")
            lines.append("")
            lines.append("| Test | Dimension | Score | Delta | Type |")
            lines.append("|------|-----------|-------|-------|------|")
            for r in critical:
                score = r.get("current_score", 0)
                delta = r.get("delta", 0)
                lines.append(
                    f"| {r['test_id']} | {r['dimension']} | {score:.3f} | {delta:+.3f} | {r['type']} |"
                )
            lines.append("")

        if warnings:
            lines.append(f"### Warnings ({len(warnings)})")
            lines.append("")
            lines.append("| Test | Dimension | Score | Delta | Type |")
            lines.append("|------|-----------|-------|-------|------|")
            for r in warnings:
                score = r.get("current_score", 0)
                delta = r.get("delta", 0)
                lines.append(
                    f"| {r['test_id']} | {r['dimension']} | {score:.3f} | {delta:+.3f} | {r['type']} |"
                )
            lines.append("")
    else:
        lines.append("## Alerts")
        lines.append("No regressions or threshold violations detected.")
        lines.append("")

    # Dimension Trends
    lines.append("## Quality Trends by Dimension")
    lines.append("")
    lines.append("| Dimension | Latest | Mean | Trend | Sparkline |")
    lines.append("|-----------|--------|------|-------|-----------|")

    dim_data = trends.get("dimensions", {})
    for dim in DIMENSIONS:
        d = dim_data.get(dim, {})
        if d.get("status") == "no_data":
            lines.append(f"| {dim} | -- | -- | no data | |")
            continue

        latest = d.get("latest", 0)
        mean = d.get("mean", 0)
        trend = d.get("trend", "?")
        trend_delta = d.get("trend_delta", 0)

        # Trend indicator
        if trend == "improving":
            trend_str = f"up ({trend_delta:+.3f})"
        elif trend == "declining":
            trend_str = f"down ({trend_delta:+.3f})"
        elif trend == "stable":
            trend_str = "stable"
        else:
            trend_str = trend

        # Build sparkline from historical data
        spark_values = []
        for entry in entries:
            for result in entry.get("results", {}).values():
                s = result.get("llm_scores", {}).get(dim)
                if s is not None:
                    spark_values.append(s)
        sparkline = generate_sparkline(spark_values, 15)

        lines.append(f"| {dim} | {latest:.3f} | {mean:.3f} | {trend_str} | `{sparkline}` |")
    lines.append("")

    # Per-Test Results (Latest)
    if entries:
        latest_entry = entries[-1]
        latest_results = latest_entry.get("results", {})

        lines.append("## Latest Test Results")
        lines.append("")
        lines.append("| Test ID | Name | Weighted | Status |")
        lines.append("|---------|------|----------|--------|")
        for test_id, result in sorted(latest_results.items()):
            name = result.get("name", "?")[:40]
            weighted = result.get("weighted_score", 0)
            passed = result.get("overall_passed", False)
            status = "PASS" if passed else "FAIL"
            lines.append(f"| {test_id} | {name} | {weighted:.3f} | {status} |")
        lines.append("")

        # Detailed scores for latest run
        lines.append("### Score Breakdown (Latest)")
        lines.append("")
        header = "| Test ID |"
        sep = "|---------|"
        for dim in DIMENSIONS:
            short_dim = dim.replace("_", " ").title()[:20]
            header += f" {short_dim} |"
            sep += "------|"
        lines.append(header)
        lines.append(sep)

        for test_id, result in sorted(latest_results.items()):
            row = f"| {test_id} |"
            scores = result.get("llm_scores", {})
            min_scores = result.get("min_scores", {})
            for dim in DIMENSIONS:
                score = scores.get(dim, 0)
                min_s = min_scores.get(dim, 0)
                marker = "" if score >= min_s else " (!)"
                row += f" {score:.3f}{marker} |"
            lines.append(row)
        lines.append("")
        lines.append("(!) = below minimum threshold")
        lines.append("")

    # Scoring Reliability
    if reliability:
        lines.append("## Scoring Reliability")
        lines.append("")
        lines.append("High coefficient of variation (CV > 0.15) suggests scoring instability.")
        lines.append("")
        lines.append("| Test | Dimension | Mean | StDev | CV | Reliable |")
        lines.append("|------|-----------|------|-------|-----|----------|")

        unreliable_count = 0
        for test_id, dims in sorted(reliability.items()):
            for dim, data in sorted(dims.items()):
                if data.get("n", 0) < 2:
                    continue
                mean = data.get("mean", 0)
                stdev = data.get("stdev", 0)
                cv = data.get("cv", 0)
                reliable = data.get("reliable", True)
                status = "yes" if reliable else "NO"
                if not reliable:
                    unreliable_count += 1
                lines.append(
                    f"| {test_id} | {dim} | {mean:.3f} | {stdev:.3f} | {cv:.3f} | {status} |"
                )
        lines.append("")
        if unreliable_count > 0:
            lines.append(
                f"**{unreliable_count} unreliable scores detected.** "
                f"Consider using `--runs 3` in judge.py for multi-run averaging."
            )
        lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")

    recommendations = []
    for dim in DIMENSIONS:
        d = dim_data.get(dim, {})
        if d.get("trend") == "declining":
            recommendations.append(
                f"- **{dim}** is declining (delta: {d.get('trend_delta', 0):+.3f}). "
                f"Review recent prompt changes that may have affected this dimension."
            )
        if d.get("latest", 1) < alert_threshold:
            recommendations.append(
                f"- **{dim}** latest score ({d.get('latest', 0):.3f}) is below alert threshold ({alert_threshold}). "
                f"Investigate root cause."
            )

    if not recommendations:
        recommendations.append("- All quality metrics are within acceptable ranges. No action needed.")

    lines.extend(recommendations)
    lines.append("")
    lines.append("---")
    lines.append("*Generated by autobiography-generator quality dashboard*")

    return "\n".join(lines)


def generate_json_dashboard(
    trends: dict,
    regressions: list[dict],
    reliability: dict,
) -> str:
    """Generate machine-readable JSON dashboard data."""
    return json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trends": trends,
        "regressions": regressions,
        "reliability": reliability,
        "summary": {
            "critical_alerts": sum(1 for r in regressions if r["severity"] == "critical"),
            "warnings": sum(1 for r in regressions if r["severity"] == "warning"),
            "dimensions_declining": sum(
                1 for d in trends.get("dimensions", {}).values()
                if d.get("trend") == "declining"
            ),
        },
    }, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Continuous Quality Dashboard")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--json", action="store_true", help="JSON output instead of markdown")
    parser.add_argument("--last", type=int, help="Only analyze last N evaluations")
    parser.add_argument("--dimension", type=str, help="Focus on specific dimension")
    parser.add_argument("--alert-threshold", type=float, default=DEFAULT_ALERT_THRESHOLD,
                        help=f"Alert threshold (default: {DEFAULT_ALERT_THRESHOLD})")
    parser.add_argument("--window", type=int, default=5,
                        help="Trend analysis window size (default: 5)")
    args = parser.parse_args()

    # Load data
    entries = load_eval_logs()
    if args.last and entries:
        entries = entries[-args.last:]

    judge_scores = load_judge_scores()
    baseline = load_latest_baseline()

    if not entries and not judge_scores:
        print("No evaluation data found.")
        print(f"Run test_quality.py first to generate evaluation data in {EVAL_LOGS_DIR}/")
        sys.exit(0)

    # Compute analytics
    trends = compute_trends(entries, window=args.window)
    regressions = detect_regressions(entries, baseline, args.alert_threshold)
    reliability = compute_test_reliability(entries)

    # Generate report
    if args.json:
        report = generate_json_dashboard(trends, regressions, reliability)
    else:
        report = generate_markdown_report(
            trends, regressions, reliability, entries, args.alert_threshold
        )

    # Output
    if args.output:
        Path(args.output).write_text(report)
        print(f"Dashboard report saved: {args.output}")
    else:
        print(report)

    # Exit with non-zero if critical regressions exist
    critical = sum(1 for r in regressions if r["severity"] == "critical")
    sys.exit(1 if critical > 0 else 0)


if __name__ == "__main__":
    main()
