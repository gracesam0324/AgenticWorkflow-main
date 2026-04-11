#!/usr/bin/env python3
"""
LLM-as-Judge Evaluator for AI Autobiography Generator.

Takes a generated chapter + evaluation criteria, calls Claude (haiku for speed)
to score on 5 quality dimensions, parses structured JSON response, returns
numeric scores, and tracks scores over time in an append-only log.

Usage:
    python3 judge.py chapter.md --transcript interview.json
    python3 judge.py chapter.md --transcript interview.json --output scores.json
    python3 judge.py --history                  # Show score history
    python3 judge.py --history --dimension emotional_authenticity

Requirements:
    - anthropic Python SDK (pip install anthropic)
    - ANTHROPIC_API_KEY environment variable set
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SCORE_LOG_DIR = SCRIPT_DIR / ".eval-logs"
SCORE_LOG_PATH = SCORE_LOG_DIR / "judge_scores.jsonl"

MODEL_JUDGE = os.environ.get("JUDGE_MODEL", "claude-haiku-4-20250514")

DIMENSIONS = {
    "emotional_authenticity": {
        "description": "Does the output honor the emotional truth of the source without amplification or diminishment?",
        "rubric": """
1 (0.0-0.2): Emotions are fabricated, melodramatic, or completely absent from the narrative
2 (0.2-0.4): Emotional register is noticeably distorted — either amplified into sentimentality or dampened into clinical detachment
3 (0.4-0.6): Captures the general mood but misses nuance — e.g., oversimplifies complex emotions into single labels
4 (0.6-0.8): Emotional truth is mostly preserved with minor drift — a sentence or two may over-dramatize or under-state
5 (0.8-1.0): Emotional register perfectly matches the source — the subject would recognize their own feelings in this text""",
    },
    "sensory_detail_preservation": {
        "description": "Are specific sensory details from the interview preserved rather than generalized?",
        "rubric": """
1 (0.0-0.2): All specific details are replaced with generic descriptions
2 (0.2-0.4): Most specific details are lost or vaguely paraphrased
3 (0.4-0.6): Some key details preserved but many are generalized (e.g., 'food' instead of 'anchovy broth')
4 (0.6-0.8): Most specific details preserved — only minor details generalized
5 (0.8-1.0): All significant sensory details from the transcript are preserved with their original specificity""",
    },
    "narrative_flow": {
        "description": "Does the prose read naturally with good pacing, transitions, and structure?",
        "rubric": """
1 (0.0-0.2): Reads like a transcript summary — no narrative arc or literary quality
2 (0.2-0.4): Choppy pacing with awkward transitions and inconsistent structure
3 (0.4-0.6): Readable but mechanical — transitions are functional rather than artful
4 (0.6-0.8): Good narrative flow with natural transitions — reads as literary prose with minor rough spots
5 (0.8-1.0): Exceptional prose with masterful pacing — builds and releases tension naturally, transitions are seamless""",
    },
    "voice_consistency": {
        "description": "Is the narrative voice consistent with the subject's speaking style and personality?",
        "rubric": """
1 (0.0-0.2): Voice sounds nothing like the subject — generic ghostwriter voice or academic writing
2 (0.2-0.4): Occasional flashes of the subject's voice but mostly overwritten
3 (0.4-0.6): Voice is recognizable but inconsistent — shifts between the subject's register and a literary voice
4 (0.6-0.8): Voice is mostly consistent and authentic — the subject's speech patterns are evident throughout
5 (0.8-1.0): Voice is indistinguishable from what the subject would write themselves — same humor, same restraint, same rhythm""",
    },
    "factual_grounding": {
        "description": "Are all facts, dates, names, and events faithful to the source transcript?",
        "rubric": """
1 (0.0-0.2): Multiple fabricated facts, invented events, or wrong names/dates
2 (0.2-0.4): Some facts are correct but significant fabrications or errors exist
3 (0.4-0.6): Most facts are correct but there are embellishments presented as fact
4 (0.6-0.8): All major facts are correct — only minor contextual additions that could be inferred
5 (0.8-1.0): 100% faithful to source — no invented facts, all details traceable to the transcript""",
    },
}


# ---------------------------------------------------------------------------
# Evaluation Prompt Builder
# ---------------------------------------------------------------------------

def build_evaluation_prompt(
    chapter_text: str,
    interview_transcript: str,
    required_elements: list[str],
    forbidden_elements: list[str],
) -> str:
    """Build the structured evaluation prompt for the judge LLM."""

    dimensions_block = ""
    for dim_name, dim_info in DIMENSIONS.items():
        dimensions_block += f"""
### {dim_name}
{dim_info['description']}

Scoring rubric:
{dim_info['rubric']}
"""

    required_block = "\n".join(f"- {r}" for r in required_elements)
    forbidden_block = "\n".join(f"- {f}" for f in forbidden_elements)

    return f"""You are an expert literary editor evaluating a generated autobiography chapter
against its source interview transcript. Score the chapter on exactly 5 dimensions.

## SOURCE INTERVIEW TRANSCRIPT
<transcript>
{interview_transcript}
</transcript>

## GENERATED CHAPTER TO EVALUATE
<chapter>
{chapter_text}
</chapter>

## REQUIRED ELEMENTS (the chapter should include these)
{required_block}

## FORBIDDEN ELEMENTS (the chapter must NOT include these)
{forbidden_block}

## SCORING DIMENSIONS
{dimensions_block}

## INSTRUCTIONS
1. Read the transcript carefully first
2. Read the generated chapter
3. For each dimension, assign a score between 0.0 and 1.0 (to 2 decimal places)
4. Provide a 1-2 sentence justification for each score
5. Note any required elements that are MISSING
6. Note any forbidden elements that are PRESENT

## RESPONSE FORMAT
Respond ONLY with valid JSON matching this exact structure:
{{
  "scores": {{
    "emotional_authenticity": <float 0.0-1.0>,
    "sensory_detail_preservation": <float 0.0-1.0>,
    "narrative_flow": <float 0.0-1.0>,
    "voice_consistency": <float 0.0-1.0>,
    "factual_grounding": <float 0.0-1.0>
  }},
  "justifications": {{
    "emotional_authenticity": "<1-2 sentence justification>",
    "sensory_detail_preservation": "<1-2 sentence justification>",
    "narrative_flow": "<1-2 sentence justification>",
    "voice_consistency": "<1-2 sentence justification>",
    "factual_grounding": "<1-2 sentence justification>"
  }},
  "missing_required": ["<element text if any are missing>"],
  "present_forbidden": ["<element text if any forbidden elements are found>"],
  "overall_notes": "<brief overall assessment>"
}}

IMPORTANT: Respond with ONLY the JSON object. No markdown fencing, no explanation outside the JSON."""


# ---------------------------------------------------------------------------
# LLM Judge Class
# ---------------------------------------------------------------------------

class LLMJudge:
    """
    Evaluator that uses Claude as a judge for autobiography chapter quality.
    """

    def __init__(self, model: Optional[str] = None):
        self.model = model or MODEL_JUDGE
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic SDK required. Run: pip install anthropic"
                )
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def evaluate(
        self,
        chapter_text: str,
        interview_transcript: str,
        required_elements: Optional[list[str]] = None,
        forbidden_elements: Optional[list[str]] = None,
        retry_count: int = 2,
    ) -> dict:
        """
        Evaluate a chapter against its source transcript.
        Returns parsed scores dictionary.
        Retries on parse failure up to retry_count times.
        """
        required_elements = required_elements or []
        forbidden_elements = forbidden_elements or []

        prompt = build_evaluation_prompt(
            chapter_text, interview_transcript,
            required_elements, forbidden_elements,
        )

        last_error = None
        for attempt in range(retry_count + 1):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw_response = message.content[0].text
                result = self._parse_response(raw_response)

                # Validate all dimensions are present
                for dim in DIMENSIONS:
                    if dim not in result["scores"]:
                        result["scores"][dim] = 0.0
                        result["justifications"][dim] = "Score not provided by judge"

                # Clamp scores to [0.0, 1.0]
                for dim in result["scores"]:
                    result["scores"][dim] = max(0.0, min(1.0, result["scores"][dim]))

                # Log the evaluation
                self._log_evaluation(result, chapter_text)

                return result

            except json.JSONDecodeError as e:
                last_error = f"JSON parse error on attempt {attempt + 1}: {e}"
                print(f"  [WARN] {last_error}")
            except Exception as e:
                last_error = f"Error on attempt {attempt + 1}: {e}"
                print(f"  [WARN] {last_error}")

        # All retries exhausted
        return {
            "scores": {dim: 0.0 for dim in DIMENSIONS},
            "justifications": {dim: "Evaluation failed" for dim in DIMENSIONS},
            "missing_required": [],
            "present_forbidden": [],
            "overall_notes": f"Judge evaluation failed after {retry_count + 1} attempts: {last_error}",
            "error": last_error,
        }

    def _parse_response(self, raw: str) -> dict:
        """
        Parse the LLM response into structured scores.
        Handles common formatting issues (markdown fencing, trailing text).
        """
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            # Remove opening fence (with optional language tag)
            raw = re.sub(r'^```\w*\n?', '', raw)
            # Remove closing fence
            raw = re.sub(r'\n?```\s*$', '', raw)

        # Try to find JSON object in the response
        # First, try parsing the whole thing
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Find first { and last }
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass

        raise json.JSONDecodeError("Could not extract JSON from response", raw, 0)

    def _log_evaluation(self, result: dict, chapter_text: str) -> None:
        """Append evaluation result to the score log (JSONL format)."""
        import hashlib
        SCORE_LOG_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model,
            "chapter_hash": hashlib.sha256(chapter_text.encode()).hexdigest()[:16],
            "chapter_words": len(chapter_text.split()),
            "scores": result["scores"],
            "justifications": result.get("justifications", {}),
            "missing_required": result.get("missing_required", []),
            "present_forbidden": result.get("present_forbidden", []),
        }
        with open(SCORE_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def evaluate_multi_run(
        self,
        chapter_text: str,
        interview_transcript: str,
        required_elements: Optional[list[str]] = None,
        forbidden_elements: Optional[list[str]] = None,
        runs: int = 3,
    ) -> dict:
        """
        Run evaluation multiple times and average scores.
        Absorbs non-deterministic variance in LLM judge scoring.
        Recommended for production baselines.
        """
        import statistics as stats

        all_scores = {dim: [] for dim in DIMENSIONS}
        all_results = []

        for i in range(runs):
            print(f"  Judge run {i + 1}/{runs}...")
            result = self.evaluate(
                chapter_text, interview_transcript,
                required_elements, forbidden_elements,
            )
            all_results.append(result)
            for dim, score in result["scores"].items():
                if dim in all_scores:
                    all_scores[dim].append(score)

        # Average scores
        avg_scores = {}
        score_stdevs = {}
        for dim, scores in all_scores.items():
            if scores:
                avg_scores[dim] = round(stats.mean(scores), 4)
                score_stdevs[dim] = round(stats.stdev(scores), 4) if len(scores) > 1 else 0.0
            else:
                avg_scores[dim] = 0.0
                score_stdevs[dim] = 0.0

        return {
            "scores": avg_scores,
            "score_stdevs": score_stdevs,
            "run_count": runs,
            "individual_runs": all_results,
            "justifications": all_results[-1].get("justifications", {}),
            "missing_required": all_results[-1].get("missing_required", []),
            "present_forbidden": all_results[-1].get("present_forbidden", []),
        }


# ---------------------------------------------------------------------------
# Score History Analysis
# ---------------------------------------------------------------------------

def load_score_history() -> list[dict]:
    """Load all historical evaluations from the JSONL log."""
    if not SCORE_LOG_PATH.exists():
        return []
    entries = []
    with open(SCORE_LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def format_history_report(entries: list[dict], dimension: Optional[str] = None) -> str:
    """Format score history as a readable report."""
    if not entries:
        return "No evaluation history found."

    lines = []
    lines.append("=" * 68)
    lines.append("  EVALUATION SCORE HISTORY")
    lines.append(f"  Total evaluations: {len(entries)}")
    lines.append("=" * 68)
    lines.append("")

    if dimension:
        # Show trend for a single dimension
        lines.append(f"  Dimension: {dimension}")
        lines.append("")
        scores = []
        for entry in entries:
            ts = entry.get("timestamp", "?")[:19]
            score = entry.get("scores", {}).get(dimension, None)
            if score is not None:
                scores.append(score)
                bar_len = int(score * 40)
                bar = "#" * bar_len + "." * (40 - bar_len)
                lines.append(f"  {ts} [{bar}] {score:.3f}")

        if scores:
            import statistics as stats
            lines.append("")
            lines.append(f"  Mean:   {stats.mean(scores):.4f}")
            lines.append(f"  Median: {stats.median(scores):.4f}")
            if len(scores) > 1:
                lines.append(f"  Stdev:  {stats.stdev(scores):.4f}")
                # Trend: compare first half to second half
                mid = len(scores) // 2
                first_half = stats.mean(scores[:mid]) if mid > 0 else 0
                second_half = stats.mean(scores[mid:])
                trend = second_half - first_half
                trend_label = "improving" if trend > 0.02 else "declining" if trend < -0.02 else "stable"
                lines.append(f"  Trend:  {trend:+.4f} ({trend_label})")
    else:
        # Show summary across all dimensions
        dim_scores = {dim: [] for dim in DIMENSIONS}
        for entry in entries:
            for dim, score in entry.get("scores", {}).items():
                if dim in dim_scores:
                    dim_scores[dim].append(score)

        lines.append(f"  {'Dimension':35s} {'Mean':>8s} {'Median':>8s} {'StDev':>8s} {'N':>5s}")
        lines.append("  " + "-" * 66)
        for dim in DIMENSIONS:
            scores = dim_scores[dim]
            if scores:
                import statistics as stats
                mean = stats.mean(scores)
                median = stats.median(scores)
                stdev = stats.stdev(scores) if len(scores) > 1 else 0
                lines.append(f"  {dim:35s} {mean:8.4f} {median:8.4f} {stdev:8.4f} {len(scores):5d}")

        # Most recent evaluation
        latest = entries[-1]
        lines.append("")
        lines.append(f"  Most recent evaluation: {latest.get('timestamp', '?')[:19]}")
        for dim, score in latest.get("scores", {}).items():
            bar_len = int(score * 30)
            bar = "#" * bar_len + "." * (30 - bar_len)
            lines.append(f"    {dim:35s} [{bar}] {score:.3f}")

    lines.append("=" * 68)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LLM-as-Judge Evaluator")
    parser.add_argument("chapter", nargs="?", help="Path to chapter text file")
    parser.add_argument("--transcript", "-t", type=str,
                        help="Path to interview transcript JSON")
    parser.add_argument("--required", type=str, nargs="*", default=[],
                        help="Required elements to check for")
    parser.add_argument("--forbidden", type=str, nargs="*", default=[],
                        help="Forbidden elements to check against")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of evaluation runs to average (default: 1)")
    parser.add_argument("--model", type=str, default=None,
                        help=f"Judge model (default: {MODEL_JUDGE})")
    parser.add_argument("--output", "-o", type=str, help="Output file for scores JSON")
    parser.add_argument("--history", action="store_true",
                        help="Show evaluation score history")
    parser.add_argument("--dimension", type=str,
                        help="Filter history to specific dimension")
    args = parser.parse_args()

    # History mode
    if args.history:
        entries = load_score_history()
        report = format_history_report(entries, args.dimension)
        print(report)
        sys.exit(0)

    # Evaluation mode
    if not args.chapter:
        parser.print_help()
        sys.exit(1)

    chapter_path = Path(args.chapter)
    if not chapter_path.exists():
        print(f"[ERROR] Chapter file not found: {chapter_path}")
        sys.exit(1)

    chapter_text = chapter_path.read_text()

    # Load transcript if provided
    transcript_text = ""
    if args.transcript:
        transcript_path = Path(args.transcript)
        if not transcript_path.exists():
            print(f"[ERROR] Transcript file not found: {transcript_path}")
            sys.exit(1)
        transcript_text = transcript_path.read_text()

    # Run evaluation
    judge = LLMJudge(model=args.model)
    print(f"Evaluating: {chapter_path.name}")
    print(f"Model: {judge.model}")
    print(f"Runs: {args.runs}")

    if args.runs > 1:
        result = judge.evaluate_multi_run(
            chapter_text, transcript_text,
            args.required, args.forbidden,
            runs=args.runs,
        )
    else:
        result = judge.evaluate(
            chapter_text, transcript_text,
            args.required, args.forbidden,
        )

    # Display results
    print("\n" + "=" * 60)
    print("  EVALUATION RESULTS")
    print("=" * 60)
    for dim, score in result["scores"].items():
        bar_len = int(score * 30)
        bar = "#" * bar_len + "." * (30 - bar_len)
        stdev_info = ""
        if "score_stdevs" in result:
            stdev_info = f" (sd={result['score_stdevs'].get(dim, 0):.3f})"
        print(f"  {dim:35s} [{bar}] {score:.3f}{stdev_info}")

    print()
    if result.get("justifications"):
        print("  Justifications:")
        for dim, just in result["justifications"].items():
            print(f"    {dim}: {just}")

    if result.get("missing_required"):
        print(f"\n  MISSING required elements:")
        for m in result["missing_required"]:
            print(f"    - {m}")

    if result.get("present_forbidden"):
        print(f"\n  PRESENT forbidden elements:")
        for p in result["present_forbidden"]:
            print(f"    - {p}")

    if result.get("overall_notes"):
        print(f"\n  Notes: {result['overall_notes']}")

    print("=" * 60)

    # Save output if requested
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
        print(f"\nScores saved: {args.output}")

    # Exit with error if any score is critically low
    critical_low = any(s < 0.3 for s in result["scores"].values())
    sys.exit(1 if critical_low else 0)


if __name__ == "__main__":
    main()
