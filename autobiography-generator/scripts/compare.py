#!/usr/bin/env python3
"""
compare.py — Side-by-Side Chapter Comparison Tool

Compares two versions of a chapter: shows diff, runs LLM-as-judge on 5 dimensions,
and outputs a markdown comparison report.

Usage:
    python3 scripts/compare.py outputs/drafts/v1.md outputs/drafts/v2.md
    python3 scripts/compare.py outputs/drafts/v1.md outputs/drafts/v2.md --source test-data/micro-interviews/INT-001-childhood.json
    python3 scripts/compare.py outputs/drafts/v1.md outputs/drafts/v2.md --no-llm   # skip LLM judge
    python3 scripts/compare.py outputs/drafts/v1.md outputs/drafts/v2.md --output outputs/comparisons/report.md

Dimensions evaluated:
    1. Voice Authenticity — Does it sound like the subject?
    2. Narrative Quality — Is it compelling, well-paced?
    3. Factual Grounding — Are claims traceable to transcripts?
    4. Emotional Resonance — Does it evoke feeling?
    5. Structural Craft — Scene openings, transitions, pacing
"""

import sys
import os
import re
import json
import argparse
import difflib
import subprocess
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Diff Analysis
# ---------------------------------------------------------------------------

def compute_diff(text_a: str, text_b: str) -> dict:
    """Compute unified diff and statistics between two texts."""
    lines_a = text_a.splitlines(keepends=True)
    lines_b = text_b.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        lines_a, lines_b,
        fromfile="version_a", tofile="version_b",
        lineterm=""
    ))

    # Count changes
    added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

    # Similarity ratio
    matcher = difflib.SequenceMatcher(None, text_a, text_b)
    similarity = matcher.ratio()

    return {
        "diff_lines": diff,
        "lines_added": added,
        "lines_removed": removed,
        "similarity_ratio": round(similarity, 3),
        "total_changes": added + removed,
    }


def compute_metrics(text: str) -> dict:
    """Compute basic text metrics."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Count direct quotes
    quotes = re.findall(r'["\u201c]([^"\u201d]{10,})["\u201d]', text)

    # First person density
    first_person = len(re.findall(r'\bI\b', text))

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "quote_count": len(quotes),
        "first_person_refs": first_person,
        "avg_sentence_length": round(len(words) / max(len(sentences), 1), 1),
    }


# ---------------------------------------------------------------------------
# LLM-as-Judge
# ---------------------------------------------------------------------------

JUDGE_PROMPT = """You are a literary critic evaluating two versions of an autobiography chapter.

## Version A
```
{version_a}
```

## Version B
```
{version_b}
```

{source_context}

Evaluate both versions on these 5 dimensions. For each dimension, score both A and B from 1-10, explain your reasoning in 1-2 sentences, and declare a winner.

## Dimensions

1. **Voice Authenticity**: Does the text sound like a real person telling their story? Is the voice distinctive and consistent? Look for natural speech patterns, characteristic phrases, and personality.

2. **Narrative Quality**: Is the prose compelling? Good pacing? Vivid scenes? Does it show rather than tell? Are transitions between topics smooth?

3. **Factual Grounding**: Are all claims, quotes, names, dates, and details grounded in the source material? Anything that seems invented?

4. **Emotional Resonance**: Does the text evoke genuine emotion? Are emotional moments earned through detail rather than stated?

5. **Structural Craft**: Does the chapter open with a scene (not exposition)? Are paragraphs well-constructed? Does it end with a bridge to the next chapter?

## Output Format
Return ONLY a JSON object:
```json
{{
  "dimensions": [
    {{
      "name": "Voice Authenticity",
      "score_a": 7,
      "score_b": 8,
      "reasoning": "...",
      "winner": "B"
    }},
    ...
  ],
  "overall_winner": "A" or "B" or "TIE",
  "overall_reasoning": "2-3 sentence summary of which version is better and why",
  "key_improvement": "The single most impactful change between versions"
}}
```
"""


def run_llm_judge(text_a: str, text_b: str, source_text: Optional[str] = None) -> Optional[dict]:
    """Run Claude as a judge to compare two chapter versions."""

    source_context = ""
    if source_text:
        # Truncate source if too long
        if len(source_text) > 8000:
            source_text = source_text[:8000] + "\n... [truncated]"
        source_context = f"""## Source Transcript (for factual grounding check)
```
{source_text}
```"""

    prompt = JUDGE_PROMPT.format(
        version_a=text_a[:6000],  # Truncate to fit context
        version_b=text_b[:6000],
        source_context=source_context,
    )

    try:
        result = subprocess.run(
            [
                "claude", "--print",
                "--model", "claude-sonnet-4-20250514",
                "--max-turns", "1",
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"[warn] LLM judge failed: {result.stderr[:200]}")
            return None

        output = result.stdout.strip()

        # Extract JSON from the output
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            return json.loads(json_match.group())
        else:
            print("[warn] Could not parse LLM judge output as JSON")
            return None

    except subprocess.TimeoutExpired:
        print("[warn] LLM judge timed out (120s)")
        return None
    except FileNotFoundError:
        print("[warn] 'claude' command not found. Install Claude Code CLI.")
        return None
    except json.JSONDecodeError as e:
        print(f"[warn] JSON parse error from LLM judge: {e}")
        return None


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(
    file_a: str,
    file_b: str,
    text_a: str,
    text_b: str,
    diff_result: dict,
    metrics_a: dict,
    metrics_b: dict,
    judge_result: Optional[dict],
) -> str:
    """Generate a markdown comparison report."""

    report = []
    report.append("# Chapter Comparison Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # ── File Info ───────────────────────────────────────────────────
    report.append("## Files Compared")
    report.append(f"- **Version A**: `{file_a}`")
    report.append(f"- **Version B**: `{file_b}`")
    report.append(f"- **Similarity**: {diff_result['similarity_ratio']:.1%}")
    report.append(f"- **Lines added**: {diff_result['lines_added']}")
    report.append(f"- **Lines removed**: {diff_result['lines_removed']}")
    report.append("")

    # ── Metrics Comparison ──────────────────────────────────────────
    report.append("## Metrics Comparison")
    report.append("")
    report.append("| Metric | Version A | Version B | Delta |")
    report.append("|--------|-----------|-----------|-------|")

    for key in metrics_a:
        val_a = metrics_a[key]
        val_b = metrics_b[key]
        if isinstance(val_a, (int, float)):
            delta = val_b - val_a
            sign = "+" if delta > 0 else ""
            report.append(f"| {key.replace('_', ' ').title()} | {val_a} | {val_b} | {sign}{delta} |")
        else:
            report.append(f"| {key.replace('_', ' ').title()} | {val_a} | {val_b} | - |")

    report.append("")

    # ── LLM Judge Results ───────────────────────────────────────────
    if judge_result:
        report.append("## LLM Judge Evaluation")
        report.append("")
        report.append("| Dimension | Score A | Score B | Winner |")
        report.append("|-----------|---------|---------|--------|")

        for dim in judge_result.get("dimensions", []):
            report.append(
                f"| {dim['name']} | {dim['score_a']}/10 | {dim['score_b']}/10 | **{dim['winner']}** |"
            )

        report.append("")

        # Dimension details
        report.append("### Detailed Reasoning")
        report.append("")
        for dim in judge_result.get("dimensions", []):
            report.append(f"**{dim['name']}**: {dim['reasoning']}")
            report.append("")

        # Overall
        report.append(f"### Overall Winner: **{judge_result.get('overall_winner', 'N/A')}**")
        report.append("")
        report.append(judge_result.get("overall_reasoning", ""))
        report.append("")

        if judge_result.get("key_improvement"):
            report.append(f"### Key Improvement")
            report.append(judge_result["key_improvement"])
            report.append("")
    else:
        report.append("## LLM Judge Evaluation")
        report.append("*Skipped (use without --no-llm to enable)*")
        report.append("")

    # ── Diff Highlights ─────────────────────────────────────────────
    report.append("## Diff Highlights (first 50 changes)")
    report.append("")
    report.append("```diff")

    diff_lines = diff_result["diff_lines"][:80]
    for line in diff_lines:
        report.append(line.rstrip())

    if len(diff_result["diff_lines"]) > 80:
        report.append(f"\n... ({len(diff_result['diff_lines']) - 80} more lines)")

    report.append("```")
    report.append("")

    return "\n".join(report)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Side-by-side chapter comparison with LLM-as-judge"
    )
    parser.add_argument("version_a", help="Path to version A (baseline)")
    parser.add_argument("version_b", help="Path to version B (candidate)")
    parser.add_argument(
        "--source", "-s",
        help="Source transcript for factual grounding check",
        default=None,
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path for the markdown report",
        default=None,
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM-as-judge evaluation (faster, metrics only)",
    )

    args = parser.parse_args()

    # Validate files
    for f in [args.version_a, args.version_b]:
        if not os.path.isfile(f):
            print(f"ERROR: File not found: {f}")
            sys.exit(1)

    print("=" * 60)
    print("  CHAPTER COMPARISON")
    print("=" * 60)
    print(f"  A: {args.version_a}")
    print(f"  B: {args.version_b}")
    print("")

    # Read files
    with open(args.version_a) as f:
        text_a = f.read()
    with open(args.version_b) as f:
        text_b = f.read()

    # Load source if provided
    source_text = None
    if args.source and os.path.isfile(args.source):
        with open(args.source) as f:
            source_text = f.read()

    # Compute diff
    print("[1/3] Computing diff...")
    diff_result = compute_diff(text_a, text_b)
    print(f"      Similarity: {diff_result['similarity_ratio']:.1%}")
    print(f"      +{diff_result['lines_added']} / -{diff_result['lines_removed']} lines")

    # Compute metrics
    print("[2/3] Computing metrics...")
    metrics_a = compute_metrics(text_a)
    metrics_b = compute_metrics(text_b)

    for key in metrics_a:
        val_a = metrics_a[key]
        val_b = metrics_b[key]
        if isinstance(val_a, (int, float)):
            delta = val_b - val_a
            sign = "+" if delta > 0 else ""
            print(f"      {key}: {val_a} -> {val_b} ({sign}{delta})")

    # LLM Judge
    judge_result = None
    if not args.no_llm:
        print("[3/3] Running LLM-as-judge (this may take 30-60s)...")
        judge_result = run_llm_judge(text_a, text_b, source_text)
        if judge_result:
            winner = judge_result.get("overall_winner", "N/A")
            print(f"      Overall winner: {winner}")
            for dim in judge_result.get("dimensions", []):
                print(f"      {dim['name']}: A={dim['score_a']}/10  B={dim['score_b']}/10  -> {dim['winner']}")
        else:
            print("      [warn] LLM judge returned no results")
    else:
        print("[3/3] LLM-as-judge skipped (--no-llm)")

    # Generate report
    report = generate_report(
        args.version_a, args.version_b,
        text_a, text_b,
        diff_result, metrics_a, metrics_b,
        judge_result,
    )

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        print(f"\n[saved] Report: {output_path}")
    else:
        # Default output path
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        default_path = f"outputs/comparisons/compare-{timestamp}.md"
        os.makedirs("outputs/comparisons", exist_ok=True)
        with open(default_path, "w") as f:
            f.write(report)
        print(f"\n[saved] Report: {default_path}")

    # Also print the report to stdout
    print("\n" + report)


if __name__ == "__main__":
    main()
