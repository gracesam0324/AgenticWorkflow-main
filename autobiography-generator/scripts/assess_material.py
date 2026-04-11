#!/usr/bin/env python3
"""Material richness scoring — episodic/dialogue/setting/sensory counts (section 22.3).

Analyzes interview transcripts (JSON per interview_transcript.schema.json) to
assess the richness and depth of source material available for each life stage.

Scores:
  - episodic_memories:  Distinct events/episodes described in detail
  - dialogue_instances: Direct quotes or reported speech from the subject
  - setting_descriptions: References to specific places with contextual detail
  - sensory_details:    Sights, sounds, smells, textures, tastes mentioned

Output:
  quality/material-assessment.json — per-life-stage depth scores and breakdown.

Usage:
    python3 scripts/assess_material.py --interviews-dir outputs/interviews/
    python3 scripts/assess_material.py --interviews-dir outputs/interviews/ --output-dir quality/

Exit codes:
    0 — assessment completed successfully
    1 — no interviews found or directory error

P1 Compliance: All validation is deterministic.
SOT Compliance: Read-only (writes only to quality/ output directory).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# Richness Indicator Patterns
# ──────────────────────────────────────────────

# Episodic memory indicators — phrases that suggest a specific recalled episode.
EPISODIC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bI remember\b",
        r"\bthere was a time\b",
        r"\bone day\b",
        r"\bthat day\b",
        r"\bthat night\b",
        r"\bthe first time\b",
        r"\bthe last time\b",
        r"\bwhen I was\b",
        r"\bback when\b",
        r"\bin those days\b",
        r"\bI recall\b",
        r"\bit happened\b",
        r"\bwe used to\b",
        r"\b그때\b",
        r"\b기억나\b",
        r"\b그날\b",
        r"\b어느 날\b",
    ]
]

# Dialogue indicators — direct speech or reported speech.
DIALOGUE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r'"[^"]{5,}"',                     # Double-quoted speech (min 5 chars)
        r"\bsaid\b",
        r"\btold me\b",
        r"\basked me\b",
        r"\bshe said\b",
        r"\bhe said\b",
        r"\bmy (?:mother|father|grandmother|grandfather) (?:said|told)\b",
        r"\b(?:말했|말씀하셨|물었|대답했)\b",
    ]
]

# Setting description indicators — specific place references with context.
SETTING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bin the (?:kitchen|room|house|garden|school|office|street|market)\b",
        r"\bat the (?:table|door|window|gate|corner|station)\b",
        r"\bthe (?:old|small|big|wooden|stone|brick) (?:house|building|room)\b",
        r"\bour (?:house|home|apartment|village|neighborhood)\b",
        r"\bthe (?:village|town|city|countryside)\b",
        r"\bdown the (?:road|street|path|hill)\b",
        r"\b(?:집|마을|학교|시장|골목|방)\b",
    ]
]

# Sensory detail indicators — sights, sounds, smells, textures, tastes.
SENSORY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in [
        # Sight
        r"\bI (?:saw|could see|watched|noticed)\b",
        r"\b(?:bright|dark|golden|red|blue|green|pale|vivid)\b",
        # Sound
        r"\bI (?:heard|could hear|listened)\b",
        r"\b(?:loud|quiet|silent|rang|echoed|hummed|whispered|shouted|cried)\b",
        # Smell
        r"\b(?:smelled|scent|aroma|fragrance|stench|odor)\b",
        r"\b(?:냄새|향기)\b",
        # Touch / texture
        r"\b(?:rough|smooth|soft|hard|warm|cold|wet|dry|sticky)\b",
        r"\b(?:touched|felt|grabbed|held|squeezed|stroked)\b",
        # Taste
        r"\b(?:tasted|sweet|bitter|sour|salty|spicy|savory|delicious)\b",
    ]
]


# ──────────────────────────────────────────────
# Life Stage Mapping
# ──────────────────────────────────────────────

def classify_life_stage(label: str, start_year: int | None, end_year: int | None) -> str:
    """Classify a life period into a standardized life stage label.

    Uses heuristics based on the period label and year range.
    """
    label_lower = label.lower()

    # Try to classify by label keywords
    if any(kw in label_lower for kw in ["childhood", "child", "어린시절", "유년"]):
        return "childhood"
    if any(kw in label_lower for kw in ["adolescen", "teen", "youth", "청소년", "사춘기", "고등학교", "중학교"]):
        return "adolescence"
    if any(kw in label_lower for kw in ["university", "college", "대학", "학부"]):
        return "young-adult"
    if any(kw in label_lower for kw in ["career", "work", "professional", "직장", "회사"]):
        return "career"
    if any(kw in label_lower for kw in ["marriage", "family", "parent", "결혼", "가정"]):
        return "family"
    if any(kw in label_lower for kw in ["retire", "later", "elder", "은퇴", "노년"]):
        return "later-life"

    # Fallback: classify by year range if birth_year is inferrable
    if start_year and end_year:
        span = end_year - start_year
        if span <= 12:
            return "childhood"
        elif span <= 18:
            return "adolescence"

    return "unclassified"


# ──────────────────────────────────────────────
# Counting Functions
# ──────────────────────────────────────────────

def count_pattern_matches(text: str, patterns: list[re.Pattern[str]]) -> int:
    """Count total matches of a list of patterns in text."""
    total = 0
    for pattern in patterns:
        total += len(pattern.findall(text))
    return total


def analyze_segment(content: str) -> dict[str, int]:
    """Analyze a single transcript segment for richness indicators.

    Args:
        content: Segment transcript text.

    Returns:
        Dictionary with counts for each indicator category.
    """
    return {
        "episodic_memories": count_pattern_matches(content, EPISODIC_PATTERNS),
        "dialogue_instances": count_pattern_matches(content, DIALOGUE_PATTERNS),
        "setting_descriptions": count_pattern_matches(content, SETTING_PATTERNS),
        "sensory_details": count_pattern_matches(content, SENSORY_PATTERNS),
    }


def compute_depth_score(indicators: dict[str, int]) -> float:
    """Compute a normalized depth score (0.0 - 1.0) from indicator counts.

    The score is a weighted combination of the four indicator categories,
    normalized against reasonable expectations per segment.

    Expected baselines per ~1000-word segment:
      episodic_memories:    ~5
      dialogue_instances:   ~3
      setting_descriptions: ~4
      sensory_details:      ~6
    """
    weights = {
        "episodic_memories": 0.35,
        "dialogue_instances": 0.25,
        "setting_descriptions": 0.20,
        "sensory_details": 0.20,
    }
    baselines = {
        "episodic_memories": 5,
        "dialogue_instances": 3,
        "setting_descriptions": 4,
        "sensory_details": 6,
    }

    weighted_sum = 0.0
    for key, weight in weights.items():
        count = indicators.get(key, 0)
        baseline = baselines[key]
        # Normalize: cap at 2x baseline to prevent single-dimension dominance.
        normalized = min(count / baseline, 2.0) / 2.0
        weighted_sum += weight * normalized

    return round(min(weighted_sum, 1.0), 3)


# ──────────────────────────────────────────────
# Main Assessment
# ──────────────────────────────────────────────

def load_interview(path: Path) -> dict | None:
    """Load a single interview transcript JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def find_interviews(interviews_dir: Path) -> list[Path]:
    """Find all JSON interview transcript files in a directory."""
    if not interviews_dir.is_dir():
        return []
    files = sorted(interviews_dir.glob("*.json"))
    return [f for f in files if f.is_file()]


def assess_material(interviews_dir: Path) -> dict[str, Any]:
    """Assess material richness across all interview transcripts.

    Args:
        interviews_dir: Path to directory containing interview JSON files.

    Returns:
        Assessment dictionary with per-life-stage scores and breakdown.
    """
    interview_files = find_interviews(interviews_dir)
    if not interview_files:
        return {
            "success": False,
            "error": f"No interview JSON files found in: {interviews_dir}",
            "life_stages": {},
            "interviews_analyzed": 0,
        }

    # Accumulate indicators per life stage.
    stage_indicators: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "episodic_memories": 0,
            "dialogue_instances": 0,
            "setting_descriptions": 0,
            "sensory_details": 0,
        }
    )
    stage_segments: dict[str, int] = defaultdict(int)
    stage_word_count: dict[str, int] = defaultdict(int)

    interviews_analyzed = 0
    warnings: list[str] = []

    for interview_path in interview_files:
        interview = load_interview(interview_path)
        if interview is None:
            warnings.append(f"Could not parse: {interview_path.name}")
            continue

        meta = interview.get("meta", {})
        life_period = meta.get("life_period", {})
        label = life_period.get("label", "unknown")
        start_year = life_period.get("start_year")
        end_year = life_period.get("end_year")

        life_stage = classify_life_stage(label, start_year, end_year)

        segments = interview.get("segments", [])
        for segment in segments:
            content = segment.get("content", "")
            if not content.strip():
                continue

            indicators = analyze_segment(content)
            for key, val in indicators.items():
                stage_indicators[life_stage][key] += val

            stage_segments[life_stage] += 1
            stage_word_count[life_stage] += len(content.split())

            # Also count key_quotes as dialogue
            key_quotes = segment.get("key_quotes", [])
            stage_indicators[life_stage]["dialogue_instances"] += len(key_quotes)

            # Count emotional_markers as potential sensory/episodic signals
            emotional_markers = segment.get("emotional_markers", [])
            stage_indicators[life_stage]["sensory_details"] += len(emotional_markers)

            # Count places_mentioned as setting descriptions
            places = segment.get("places_mentioned", [])
            stage_indicators[life_stage]["setting_descriptions"] += len(places)

            # Count events as episodic memories
            events = segment.get("events", [])
            stage_indicators[life_stage]["episodic_memories"] += len(events)

        interviews_analyzed += 1

    # Compute per-stage depth scores.
    life_stages: dict[str, dict[str, Any]] = {}
    for stage in sorted(stage_indicators.keys()):
        indicators = stage_indicators[stage]
        depth_score = compute_depth_score(indicators)
        life_stages[stage] = {
            "depth_score": depth_score,
            "segments_count": stage_segments[stage],
            "word_count": stage_word_count[stage],
            "indicators": indicators,
        }

    # Overall summary.
    all_scores = [ls["depth_score"] for ls in life_stages.values()]
    overall_score = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0.0

    return {
        "success": True,
        "interviews_analyzed": interviews_analyzed,
        "overall_depth_score": overall_score,
        "life_stages": life_stages,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assess material richness from interview transcripts"
    )
    parser.add_argument(
        "--interviews-dir", required=True,
        help="Path to directory containing interview transcript JSON files"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory for material-assessment.json (default: quality/ under project root)"
    )
    args = parser.parse_args()

    interviews_dir = Path(args.interviews_dir).resolve()
    result = assess_material(interviews_dir)

    if not result["success"]:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Determine output path.
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        # Default: quality/ directory relative to the interviews dir's parent project
        output_dir = interviews_dir.parent.parent / "quality"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "material-assessment.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Print summary.
    print("Material Richness Assessment")
    print("=" * 55)
    print(f"  Interviews analyzed: {result['interviews_analyzed']}")
    print(f"  Overall depth score: {result['overall_depth_score']:.3f}")
    print()

    for stage, data in result["life_stages"].items():
        indicators = data["indicators"]
        print(f"  [{stage}]")
        print(f"    Depth score:     {data['depth_score']:.3f}")
        print(f"    Segments:        {data['segments_count']}")
        print(f"    Word count:      {data['word_count']:,}")
        print(f"    Episodic:        {indicators['episodic_memories']}")
        print(f"    Dialogue:        {indicators['dialogue_instances']}")
        print(f"    Settings:        {indicators['setting_descriptions']}")
        print(f"    Sensory:         {indicators['sensory_details']}")
        print()

    if result.get("warnings"):
        print("Warnings:")
        for w in result["warnings"]:
            print(f"  - {w}")
        print()

    print(f"Output written to: {output_path}")
    print("=" * 55)

    sys.exit(0)


if __name__ == "__main__":
    main()
