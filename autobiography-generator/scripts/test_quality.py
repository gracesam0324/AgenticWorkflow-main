#!/usr/bin/env python3
"""
Automated Quality Test Runner for AI Autobiography Generator.

Loads golden test cases, runs each through the pipeline, evaluates output
against criteria using both deterministic checks and LLM-as-judge scoring,
produces a test report, and flags regressions vs baseline.

Usage:
    python3 test_quality.py                       # Run all tests
    python3 test_quality.py --test-id GT-001      # Run single test
    python3 test_quality.py --baseline             # Save current run as baseline
    python3 test_quality.py --compare-baseline     # Compare against saved baseline
    python3 test_quality.py --report-format html   # Output format (text|json|html)

Requirements:
    - anthropic Python SDK (pip install anthropic)
    - ANTHROPIC_API_KEY environment variable set
"""

import json
import os
import sys
import re
import hashlib
import statistics
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
GOLDEN_DATA_PATH = SCRIPT_DIR / "golden_test_data.json"
BASELINE_DIR = SCRIPT_DIR / ".quality-baselines"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reviews"
EVAL_LOGS_DIR = SCRIPT_DIR / ".eval-logs"

MODEL_GENERATE = "claude-sonnet-4-20250514"   # generation model
MODEL_JUDGE = "claude-haiku-4-20250514"       # evaluation model (fast + cheap)

# ---------------------------------------------------------------------------
# Pipeline Simulation (replace with actual pipeline call in production)
# ---------------------------------------------------------------------------

def call_generation_pipeline(interview_json: dict) -> str:
    """
    Call the autobiography generation pipeline with an interview transcript.
    Returns the generated chapter text.

    In production, this calls the actual Claude-based generation pipeline.
    For testing without API keys, returns a marker for dry-run mode.
    """
    try:
        import anthropic
    except ImportError:
        print("[WARN] anthropic SDK not installed. Run: pip install anthropic")
        print("[WARN] Falling back to dry-run mode.")
        return _dry_run_generate(interview_json)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[WARN] ANTHROPIC_API_KEY not set. Falling back to dry-run mode.")
        return _dry_run_generate(interview_json)

    client = anthropic.Anthropic(api_key=api_key)

    # Build the generation prompt from the interview transcript
    subject = interview_json["meta"]["subject_name"]
    period = interview_json["meta"]["life_period"]["label"]
    tone = interview_json["meta"].get("emotional_tone", "reflective")
    themes = ", ".join(interview_json["meta"].get("themes", []))

    segments_text = ""
    for seg in interview_json["segments"]:
        segments_text += f"\n### {seg['topic']}\n{seg['content']}\n"
        if seg.get("key_quotes"):
            segments_text += "\nKey quotes to preserve:\n"
            for q in seg["key_quotes"]:
                segments_text += f'- "{q["text"]}"\n'

    prompt = f"""You are a skilled literary ghostwriter transforming interview transcripts
into autobiography chapters. Write a chapter based on the following interview transcript.

SUBJECT: {subject}
PERIOD: {period}
DOMINANT TONE: {tone}
THEMES: {themes}

INTERVIEW TRANSCRIPT:
{segments_text}

INSTRUCTIONS:
- Write in first person from the subject's perspective
- Preserve the subject's authentic voice and speech patterns
- Keep all specific details (names, dates, places, numbers) faithful to the source
- Preserve key quotes verbatim or near-verbatim when they are powerful
- Do NOT invent new events, characters, or dialogue not in the transcript
- Do NOT impose external frameworks (psychological, cultural stereotypes)
- Do NOT add cliches or sentimentality not present in the source
- Maintain the emotional register of the original — do not amplify or diminish
- Aim for 800-1200 words

Write the chapter now."""

    message = client.messages.create(
        model=MODEL_GENERATE,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _dry_run_generate(interview_json: dict) -> str:
    """Return a placeholder for dry-run testing without API access."""
    seg = interview_json["segments"][0]
    return (
        f"[DRY-RUN CHAPTER]\n\n"
        f"Based on interview about: {seg['topic']}\n\n"
        f"{seg['content']}\n\n"
        f"[This is a dry-run output. Set ANTHROPIC_API_KEY for real generation.]"
    )


# ---------------------------------------------------------------------------
# Deterministic Quality Checks
# ---------------------------------------------------------------------------

class DeterministicChecker:
    """Runs rule-based checks that don't require an LLM."""

    @staticmethod
    def check_required_elements(
        chapter_text: str, required_elements: list[str], key_quotes: list[dict]
    ) -> dict:
        """Check whether required structural/content elements are present."""
        results = []
        quote_texts = [q["text"] for q in key_quotes if q.get("usable_in_chapter", True)]

        # Check for at least one key quote preserved (fuzzy match)
        quotes_found = 0
        for qt in quote_texts:
            # Allow near-match: 80% of words in order
            qt_words = qt.lower().split()
            threshold = int(len(qt_words) * 0.6)
            chapter_lower = chapter_text.lower()
            matches = sum(1 for w in qt_words if w in chapter_lower)
            if matches >= threshold:
                quotes_found += 1

        results.append({
            "check": "key_quote_preservation",
            "passed": quotes_found > 0,
            "detail": f"{quotes_found}/{len(quote_texts)} key quotes found (need >= 1)",
        })

        # Check factual elements (names, places, dates from transcript)
        return {
            "checks": results,
            "pass_rate": sum(1 for r in results if r["passed"]) / max(len(results), 1),
        }

    @staticmethod
    def check_forbidden_patterns(chapter_text: str, forbidden_elements: list[str]) -> dict:
        """Check for common forbidden patterns via regex."""
        cliche_patterns = [
            r"those were the best days",
            r"little did (I|he|she|they) know",
            r"everything happens for a reason",
            r"it was meant to be",
            r"if only I had known",
            r"the american dream",
            r"rags to riches",
            r"against all odds",
            r"a blessing in disguise",
        ]
        violations = []
        chapter_lower = chapter_text.lower()
        for pattern in cliche_patterns:
            if re.search(pattern, chapter_lower):
                violations.append(f"Cliche detected: '{pattern}'")

        # Check for invented dialogue markers (excessive quotes not in source)
        dialogue_chunks = re.findall(r'"[^"]{20,}"', chapter_text)
        if len(dialogue_chunks) > 10:
            violations.append(
                f"Excessive dialogue ({len(dialogue_chunks)} chunks) — may contain invented speech"
            )

        return {
            "violations": violations,
            "passed": len(violations) == 0,
            "detail": f"{len(violations)} forbidden pattern violations",
        }

    @staticmethod
    def check_structural_quality(chapter_text: str) -> dict:
        """Check basic structural quality metrics."""
        sentences = re.split(r'[.!?]+', chapter_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        words = chapter_text.split()
        paragraphs = [p.strip() for p in chapter_text.split("\n\n") if p.strip()]

        word_count = len(words)
        sentence_count = len(sentences)
        paragraph_count = len(paragraphs)
        avg_sentence_length = word_count / max(sentence_count, 1)

        # Sentence length variance (good writing has variety)
        sent_lengths = [len(s.split()) for s in sentences]
        sent_length_std = statistics.stdev(sent_lengths) if len(sent_lengths) > 1 else 0

        checks = []

        # Word count within range
        checks.append({
            "check": "word_count_range",
            "passed": 300 <= word_count <= 2500,
            "detail": f"{word_count} words (target: 300-2500)",
        })

        # Paragraph count (at least 3)
        checks.append({
            "check": "paragraph_count",
            "passed": paragraph_count >= 3,
            "detail": f"{paragraph_count} paragraphs (need >= 3)",
        })

        # Sentence length variety (std > 3 words)
        checks.append({
            "check": "sentence_variety",
            "passed": sent_length_std > 3.0,
            "detail": f"Sentence length std: {sent_length_std:.1f} (need > 3.0)",
        })

        # Average sentence length (not too short, not too long)
        checks.append({
            "check": "avg_sentence_length",
            "passed": 10 <= avg_sentence_length <= 30,
            "detail": f"Avg sentence: {avg_sentence_length:.1f} words (target: 10-30)",
        })

        return {
            "checks": checks,
            "metrics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_sentence_length": round(avg_sentence_length, 1),
                "sentence_length_std": round(sent_length_std, 1),
            },
            "pass_rate": sum(1 for c in checks if c["passed"]) / max(len(checks), 1),
        }


# ---------------------------------------------------------------------------
# LLM-as-Judge Evaluation (delegates to judge.py)
# ---------------------------------------------------------------------------

def run_llm_judge(chapter_text: str, test_case: dict) -> dict:
    """
    Call the LLM judge to score the chapter on 5 quality dimensions.
    Imports from judge.py to avoid code duplication.
    """
    try:
        # Try importing the judge module from the same directory
        sys.path.insert(0, str(SCRIPT_DIR))
        from judge import LLMJudge
        judge = LLMJudge()
        return judge.evaluate(
            chapter_text=chapter_text,
            interview_transcript=json.dumps(test_case["interview_excerpt"], indent=2),
            required_elements=test_case["expected_quality"]["required_elements"],
            forbidden_elements=test_case["expected_quality"]["forbidden_elements"],
        )
    except ImportError:
        print("[WARN] judge.py not found or not importable. Skipping LLM evaluation.")
        return {
            "scores": {dim: 0.0 for dim in test_case["expected_quality"]["min_scores"]},
            "error": "judge.py not available",
        }
    except Exception as e:
        print(f"[WARN] LLM judge error: {e}")
        return {
            "scores": {dim: 0.0 for dim in test_case["expected_quality"]["min_scores"]},
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Regression Detection
# ---------------------------------------------------------------------------

class RegressionDetector:
    """Compare current results against saved baselines."""

    def __init__(self, baseline_dir: Path):
        self.baseline_dir = baseline_dir
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def save_baseline(self, results: dict) -> Path:
        """Save current results as the new baseline."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.baseline_dir / f"baseline_{ts}.json"
        # Also maintain a 'latest' symlink/copy
        latest = self.baseline_dir / "baseline_latest.json"
        data = {
            "timestamp": ts,
            "results": results,
        }
        path.write_text(json.dumps(data, indent=2))
        latest.write_text(json.dumps(data, indent=2))
        return path

    def load_latest_baseline(self) -> Optional[dict]:
        """Load the most recent baseline."""
        latest = self.baseline_dir / "baseline_latest.json"
        if not latest.exists():
            return None
        return json.loads(latest.read_text())

    def compare(self, current: dict, baseline: dict, thresholds: dict) -> dict:
        """
        Compare current scores against baseline.
        Returns regression report with alerts and blocks.
        """
        regressions = []
        improvements = []
        delta_alert = thresholds.get("regression_delta_alert", -0.05)
        delta_block = thresholds.get("regression_delta_block", -0.10)

        for test_id, current_result in current.items():
            if test_id not in baseline:
                continue
            baseline_result = baseline[test_id]

            current_scores = current_result.get("llm_scores", {})
            baseline_scores = baseline_result.get("llm_scores", {})

            for dim, curr_score in current_scores.items():
                base_score = baseline_scores.get(dim, curr_score)
                delta = curr_score - base_score
                entry = {
                    "test_id": test_id,
                    "dimension": dim,
                    "baseline": round(base_score, 3),
                    "current": round(curr_score, 3),
                    "delta": round(delta, 3),
                }
                if delta <= delta_block:
                    entry["severity"] = "BLOCK"
                    regressions.append(entry)
                elif delta <= delta_alert:
                    entry["severity"] = "ALERT"
                    regressions.append(entry)
                elif delta > 0.05:
                    improvements.append(entry)

        should_block = any(r["severity"] == "BLOCK" for r in regressions)
        return {
            "regressions": regressions,
            "improvements": improvements,
            "should_block": should_block,
            "summary": (
                f"{len(regressions)} regressions ({sum(1 for r in regressions if r['severity'] == 'BLOCK')} blocking), "
                f"{len(improvements)} improvements"
            ),
        }


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_text_report(results: dict, regression_report: Optional[dict] = None) -> str:
    """Generate a human-readable text report."""
    lines = []
    lines.append("=" * 72)
    lines.append("  AI AUTOBIOGRAPHY GENERATOR — QUALITY TEST REPORT")
    lines.append(f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("=" * 72)
    lines.append("")

    overall_pass = 0
    overall_fail = 0

    for test_id, result in sorted(results.items()):
        passed = result.get("overall_passed", False)
        if passed:
            overall_pass += 1
        else:
            overall_fail += 1

        status = "PASS" if passed else "FAIL"
        lines.append(f"--- [{status}] {test_id}: {result.get('name', 'Unknown')} ---")
        lines.append(f"  Life stage: {result.get('life_stage', '?')}")
        lines.append(f"  Emotional depth: {result.get('emotional_depth', '?')}")
        lines.append(f"  Pass threshold: {result.get('pass_threshold', '?')}")
        lines.append("")

        # Deterministic checks
        det = result.get("deterministic", {})
        lines.append("  Deterministic Checks:")
        for section_name, section_data in det.items():
            if isinstance(section_data, dict):
                checks = section_data.get("checks", [])
                for chk in checks:
                    mark = "OK" if chk.get("passed") else "XX"
                    lines.append(f"    [{mark}] {chk.get('check', '?')}: {chk.get('detail', '')}")
                violations = section_data.get("violations", [])
                for v in violations:
                    lines.append(f"    [XX] {v}")
        lines.append("")

        # LLM scores
        llm_scores = result.get("llm_scores", {})
        min_scores = result.get("min_scores", {})
        if llm_scores:
            lines.append("  LLM Judge Scores:")
            for dim, score in llm_scores.items():
                min_s = min_scores.get(dim, 0)
                mark = "OK" if score >= min_s else "XX"
                lines.append(f"    [{mark}] {dim}: {score:.3f} (min: {min_s:.2f})")
            weighted = result.get("weighted_score", 0)
            lines.append(f"  Weighted score: {weighted:.3f}")
        lines.append("")

    # Summary
    total = overall_pass + overall_fail
    lines.append("=" * 72)
    lines.append(f"  SUMMARY: {overall_pass}/{total} tests passed")
    if total > 0:
        lines.append(f"  Pass rate: {overall_pass/total*100:.1f}%")
    lines.append("=" * 72)

    # Regression report
    if regression_report:
        lines.append("")
        lines.append("--- REGRESSION ANALYSIS ---")
        lines.append(f"  {regression_report['summary']}")
        if regression_report["regressions"]:
            lines.append("")
            for r in regression_report["regressions"]:
                lines.append(
                    f"  [{r['severity']}] {r['test_id']}/{r['dimension']}: "
                    f"{r['baseline']:.3f} -> {r['current']:.3f} (delta: {r['delta']:+.3f})"
                )
        if regression_report["improvements"]:
            lines.append("")
            lines.append("  Improvements:")
            for imp in regression_report["improvements"]:
                lines.append(
                    f"  [UP] {imp['test_id']}/{imp['dimension']}: "
                    f"{imp['baseline']:.3f} -> {imp['current']:.3f} (delta: {imp['delta']:+.3f})"
                )
        if regression_report["should_block"]:
            lines.append("")
            lines.append("  *** BLOCKING REGRESSIONS DETECTED — COMMIT SHOULD BE BLOCKED ***")

    return "\n".join(lines)


def generate_json_report(results: dict, regression_report: Optional[dict] = None) -> str:
    """Generate a JSON report for programmatic consumption."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "regression": regression_report,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results.values() if r.get("overall_passed")),
            "failed": sum(1 for r in results.values() if not r.get("overall_passed")),
        },
    }
    return json.dumps(report, indent=2)


# ---------------------------------------------------------------------------
# Main Test Runner
# ---------------------------------------------------------------------------

def run_test(test_case: dict, scoring_dims: dict) -> dict:
    """Run a single golden test case through the full pipeline."""
    test_id = test_case["id"]
    print(f"\n[RUN] {test_id}: {test_case['name']}")

    # Step 1: Generate chapter from interview transcript
    print(f"  Generating chapter...")
    chapter_text = call_generation_pipeline(test_case["interview_excerpt"])
    print(f"  Generated {len(chapter_text.split())} words")

    # Step 2: Run deterministic checks
    print(f"  Running deterministic checks...")
    key_quotes = []
    for seg in test_case["interview_excerpt"]["segments"]:
        key_quotes.extend(seg.get("key_quotes", []))

    det_required = DeterministicChecker.check_required_elements(
        chapter_text,
        test_case["expected_quality"]["required_elements"],
        key_quotes,
    )
    det_forbidden = DeterministicChecker.check_forbidden_patterns(
        chapter_text,
        test_case["expected_quality"]["forbidden_elements"],
    )
    det_structure = DeterministicChecker.check_structural_quality(chapter_text)

    # Step 3: Run LLM-as-judge evaluation
    print(f"  Running LLM judge evaluation...")
    llm_result = run_llm_judge(chapter_text, test_case)
    llm_scores = llm_result.get("scores", {})

    # Step 4: Calculate weighted score
    weighted_score = 0.0
    total_weight = 0.0
    for dim, weight_info in scoring_dims.items():
        weight = weight_info["weight"]
        score = llm_scores.get(dim, 0.0)
        weighted_score += score * weight
        total_weight += weight
    if total_weight > 0:
        weighted_score /= total_weight

    # Step 5: Determine pass/fail
    threshold = test_case["pass_threshold"]
    min_scores = test_case["expected_quality"]["min_scores"]
    all_mins_met = all(
        llm_scores.get(dim, 0) >= min_s for dim, min_s in min_scores.items()
    )
    det_passed = (
        det_required["pass_rate"] >= 0.5
        and det_forbidden["passed"]
        and det_structure["pass_rate"] >= 0.5
    )
    overall_passed = weighted_score >= threshold and all_mins_met and det_passed

    status = "PASS" if overall_passed else "FAIL"
    print(f"  Result: [{status}] weighted={weighted_score:.3f} threshold={threshold}")

    return {
        "name": test_case["name"],
        "life_stage": test_case["life_stage"],
        "emotional_depth": test_case["emotional_depth"],
        "pass_threshold": threshold,
        "overall_passed": overall_passed,
        "weighted_score": round(weighted_score, 4),
        "llm_scores": {k: round(v, 4) for k, v in llm_scores.items()},
        "min_scores": min_scores,
        "deterministic": {
            "required_elements": det_required,
            "forbidden_patterns": det_forbidden,
            "structural_quality": det_structure,
        },
        "chapter_hash": hashlib.sha256(chapter_text.encode()).hexdigest()[:16],
        "chapter_word_count": len(chapter_text.split()),
        "generated_text_preview": chapter_text[:500] + "..." if len(chapter_text) > 500 else chapter_text,
    }


def main():
    parser = argparse.ArgumentParser(description="Quality Test Runner for AI Autobiography Generator")
    parser.add_argument("--test-id", type=str, help="Run specific test by ID (e.g., GT-001)")
    parser.add_argument("--baseline", action="store_true", help="Save current run as baseline")
    parser.add_argument("--compare-baseline", action="store_true", help="Compare against saved baseline")
    parser.add_argument("--report-format", choices=["text", "json", "html"], default="text")
    parser.add_argument("--output", type=str, help="Output file path (default: stdout)")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls, use placeholder output")
    args = parser.parse_args()

    # Load golden test data
    if not GOLDEN_DATA_PATH.exists():
        print(f"[ERROR] Golden test data not found: {GOLDEN_DATA_PATH}")
        sys.exit(1)

    golden_data = json.loads(GOLDEN_DATA_PATH.read_text())
    test_cases = golden_data["test_cases"]
    scoring_dims = golden_data["scoring_dimensions"]
    global_thresholds = golden_data["global_thresholds"]

    # Filter to specific test if requested
    if args.test_id:
        test_cases = [tc for tc in test_cases if tc["id"] == args.test_id]
        if not test_cases:
            print(f"[ERROR] Test case {args.test_id} not found")
            sys.exit(1)

    # Run all tests
    print(f"Running {len(test_cases)} golden test(s)...")
    results = {}
    for tc in test_cases:
        result = run_test(tc, scoring_dims)
        results[tc["id"]] = result

    # Save eval log
    EVAL_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = EVAL_LOGS_DIR / f"eval_{ts}.json"
    log_path.write_text(json.dumps({"timestamp": ts, "results": results}, indent=2))
    print(f"\nEval log saved: {log_path}")

    # Regression detection
    regression_report = None
    detector = RegressionDetector(BASELINE_DIR)

    if args.baseline:
        bp = detector.save_baseline(results)
        print(f"Baseline saved: {bp}")

    if args.compare_baseline:
        baseline_data = detector.load_latest_baseline()
        if baseline_data:
            regression_report = detector.compare(
                results, baseline_data["results"], global_thresholds
            )
        else:
            print("[WARN] No baseline found. Run with --baseline first.")

    # Generate report
    if args.report_format == "json":
        report = generate_json_report(results, regression_report)
    else:
        report = generate_text_report(results, regression_report)

    if args.output:
        Path(args.output).write_text(report)
        print(f"Report saved: {args.output}")
    else:
        print(report)

    # Exit code: non-zero if any test failed or blocking regression
    any_failed = any(not r.get("overall_passed") for r in results.values())
    should_block = regression_report and regression_report.get("should_block", False)
    if any_failed or should_block:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
