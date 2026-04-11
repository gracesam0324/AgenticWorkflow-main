#!/usr/bin/env python3
"""
Voice Consistency Checker for AI Autobiography Generator.

Extracts stylistic features from text (sentence length distribution, vocabulary
richness, formality score, rhetorical patterns) and compares chapters for voice
similarity. Outputs a similarity score (0.0-1.0) and flags chapters below threshold.

All analysis is stdlib-only — no external NLP libraries required. This makes it
runnable in any environment without dependency installation.

Usage:
    python3 check_voice.py chapter1.md chapter2.md
    python3 check_voice.py --directory outputs/chapters/
    python3 check_voice.py --reference story-bible/voice-profile.json chapter3.md
    python3 check_voice.py chapter1.md chapter2.md --threshold 0.70
"""

import json
import math
import os
import re
import sys
import argparse
import statistics
from collections import Counter
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Feature Extraction
# ---------------------------------------------------------------------------

# Common English contractions (informal markers)
CONTRACTIONS = {
    "i'm", "i've", "i'd", "i'll", "we're", "we've", "we'd", "we'll",
    "you're", "you've", "you'd", "you'll", "they're", "they've", "they'd",
    "they'll", "he's", "she's", "it's", "that's", "there's", "here's",
    "who's", "what's", "where's", "when's", "how's", "can't", "won't",
    "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't",
    "hasn't", "haven't", "hadn't", "couldn't", "wouldn't", "shouldn't",
    "mustn't", "let's", "ain't", "gonna", "wanna", "gotta",
}

# Formal register markers
FORMAL_MARKERS = {
    "therefore", "furthermore", "moreover", "nevertheless", "consequently",
    "notwithstanding", "accordingly", "henceforth", "whereby", "thereof",
    "wherein", "herein", "thus", "hence", "albeit", "inasmuch",
    "subsequent", "preceding", "aforementioned", "pursuant",
}

# Transition words/phrases
TRANSITIONS = {
    "however", "but", "although", "yet", "still", "meanwhile", "then",
    "afterwards", "later", "before", "after", "finally", "eventually",
    "suddenly", "gradually", "slowly", "quickly", "immediately",
    "in the end", "at last", "by then", "looking back",
}

# Emotional/reflective language
REFLECTIVE_MARKERS = {
    "remember", "recall", "looking back", "in hindsight", "now I realize",
    "I didn't know then", "years later", "it occurs to me", "I wonder",
    "perhaps", "maybe", "somehow", "I think", "I believe", "I suppose",
    "I imagine", "it seems", "it felt", "I felt",
}

# Sensory language categories
SENSORY_WORDS = {
    "visual": {"see", "saw", "looked", "watched", "glanced", "stared", "bright",
               "dark", "color", "shadow", "light", "gleam", "shimmer", "vivid"},
    "auditory": {"hear", "heard", "listen", "sound", "noise", "whisper", "shout",
                 "ring", "echo", "silence", "quiet", "loud", "hum", "rhythm"},
    "tactile": {"touch", "felt", "cold", "warm", "hot", "smooth", "rough",
                "soft", "hard", "wet", "dry", "sharp", "gentle", "grip"},
    "olfactory": {"smell", "scent", "aroma", "odor", "fragrant", "stink",
                  "whiff", "perfume", "fresh", "musty"},
    "gustatory": {"taste", "tasted", "sweet", "bitter", "sour", "salty",
                  "flavor", "delicious", "bland", "savory"},
}


def tokenize_sentences(text: str) -> list[str]:
    """Split text into sentences using regex-based heuristics."""
    # Handle common abbreviations to avoid false splits
    text = re.sub(r'Mr\.', 'Mr', text)
    text = re.sub(r'Mrs\.', 'Mrs', text)
    text = re.sub(r'Dr\.', 'Dr', text)
    text = re.sub(r'Jr\.', 'Jr', text)
    text = re.sub(r'Sr\.', 'Sr', text)
    text = re.sub(r'vs\.', 'vs', text)
    text = re.sub(r'e\.g\.', 'eg', text)
    text = re.sub(r'i\.e\.', 'ie', text)

    # Split on sentence-ending punctuation followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', text)
    # Also split on explicit line breaks that start new paragraphs
    expanded = []
    for s in sentences:
        parts = re.split(r'\n\s*\n', s)
        expanded.extend(parts)

    return [s.strip() for s in expanded if len(s.strip()) > 5]


def tokenize_words(text: str) -> list[str]:
    """Extract words from text, lowercased."""
    return re.findall(r"[a-z']+", text.lower())


def extract_features(text: str) -> dict:
    """
    Extract comprehensive stylistic features from a text.
    Returns a feature dictionary suitable for comparison.
    """
    sentences = tokenize_sentences(text)
    words = tokenize_words(text)
    word_count = len(words)
    sentence_count = len(sentences)

    if word_count < 10 or sentence_count < 2:
        return {"error": "Text too short for meaningful analysis", "word_count": word_count}

    word_freq = Counter(words)
    unique_words = len(word_freq)

    # --- Sentence Length Distribution ---
    sent_lengths = [len(tokenize_words(s)) for s in sentences]
    sl_mean = statistics.mean(sent_lengths)
    sl_median = statistics.median(sent_lengths)
    sl_stdev = statistics.stdev(sent_lengths) if len(sent_lengths) > 1 else 0
    sl_skew = (sl_mean - sl_median) / max(sl_stdev, 0.01)

    # Sentence length histogram (binned)
    short = sum(1 for l in sent_lengths if l < 10) / sentence_count
    medium = sum(1 for l in sent_lengths if 10 <= l < 20) / sentence_count
    long_s = sum(1 for l in sent_lengths if 20 <= l < 35) / sentence_count
    very_long = sum(1 for l in sent_lengths if l >= 35) / sentence_count

    # --- Vocabulary Richness ---
    ttr = unique_words / word_count  # Type-Token Ratio
    # Root TTR (Guiraud's index) — more stable for different text lengths
    rttr = unique_words / math.sqrt(word_count)
    # Hapax legomena ratio (words appearing exactly once)
    hapax = sum(1 for w, c in word_freq.items() if c == 1) / unique_words

    # --- Formality Score ---
    contraction_count = sum(1 for w in words if w in CONTRACTIONS)
    formal_count = sum(1 for w in words if w in FORMAL_MARKERS)
    contraction_rate = contraction_count / word_count
    formal_rate = formal_count / word_count
    # Formality: 0.0 = very informal, 1.0 = very formal
    formality = 0.5 + (formal_rate * 50) - (contraction_rate * 50)
    formality = max(0.0, min(1.0, formality))

    # --- Punctuation Profile ---
    em_dash_count = text.count("—") + text.count(" -- ")
    ellipsis_count = text.count("...") + text.count("…")
    question_count = text.count("?")
    exclamation_count = text.count("!")
    semicolon_count = text.count(";")
    colon_count = text.count(":")
    paren_count = text.count("(")

    punct_per_sent = {
        "em_dash": em_dash_count / sentence_count,
        "ellipsis": ellipsis_count / sentence_count,
        "question": question_count / sentence_count,
        "exclamation": exclamation_count / sentence_count,
        "semicolon": semicolon_count / sentence_count,
        "colon": colon_count / sentence_count,
        "parenthetical": paren_count / sentence_count,
    }

    # --- Paragraph Structure ---
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    para_lengths = [len(tokenize_words(p)) for p in paragraphs]
    para_mean = statistics.mean(para_lengths) if para_lengths else 0
    para_stdev = statistics.stdev(para_lengths) if len(para_lengths) > 1 else 0

    # --- Rhetorical Patterns ---
    transition_count = 0
    text_lower = text.lower()
    for t in TRANSITIONS:
        transition_count += text_lower.count(t)
    transition_rate = transition_count / sentence_count

    reflective_count = 0
    for r in REFLECTIVE_MARKERS:
        reflective_count += text_lower.count(r)
    reflective_rate = reflective_count / sentence_count

    # --- Sensory Language Profile ---
    sensory_profile = {}
    for category, word_set in SENSORY_WORDS.items():
        count = sum(1 for w in words if w in word_set)
        sensory_profile[category] = count / word_count

    # --- Opening Pattern ---
    first_word = words[0] if words else ""
    first_sentence_len = sent_lengths[0] if sent_lengths else 0

    # --- Dialogue Density ---
    dialogue_chunks = re.findall(r'"[^"]*"', text)
    dialogue_words = sum(len(tokenize_words(d)) for d in dialogue_chunks)
    dialogue_ratio = dialogue_words / word_count

    # --- First Person Density ---
    first_person = sum(1 for w in words if w in {"i", "me", "my", "mine", "myself"})
    first_person_rate = first_person / word_count

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "sentence_length": {
            "mean": round(sl_mean, 2),
            "median": round(sl_median, 2),
            "stdev": round(sl_stdev, 2),
            "skew": round(sl_skew, 3),
            "distribution": {
                "short_pct": round(short, 3),
                "medium_pct": round(medium, 3),
                "long_pct": round(long_s, 3),
                "very_long_pct": round(very_long, 3),
            },
        },
        "vocabulary": {
            "ttr": round(ttr, 4),
            "rttr": round(rttr, 4),
            "hapax_ratio": round(hapax, 4),
            "unique_words": unique_words,
        },
        "formality": {
            "score": round(formality, 4),
            "contraction_rate": round(contraction_rate, 5),
            "formal_marker_rate": round(formal_rate, 5),
        },
        "punctuation": {k: round(v, 4) for k, v in punct_per_sent.items()},
        "paragraph": {
            "count": len(paragraphs),
            "mean_length": round(para_mean, 1),
            "stdev_length": round(para_stdev, 1),
        },
        "rhetoric": {
            "transition_rate": round(transition_rate, 4),
            "reflective_rate": round(reflective_rate, 4),
        },
        "sensory_profile": {k: round(v, 5) for k, v in sensory_profile.items()},
        "dialogue_ratio": round(dialogue_ratio, 4),
        "first_person_rate": round(first_person_rate, 4),
    }


# ---------------------------------------------------------------------------
# Voice Comparison
# ---------------------------------------------------------------------------

def compute_similarity(features_a: dict, features_b: dict) -> dict:
    """
    Compare two feature sets and produce a similarity score (0.0-1.0).
    Uses weighted cosine-like similarity across multiple feature dimensions.
    """
    if "error" in features_a or "error" in features_b:
        return {"score": 0.0, "error": "One or both texts too short", "breakdown": {}}

    dimension_scores = {}

    # 1. Sentence length distribution similarity (weight: 0.20)
    sl_a = features_a["sentence_length"]
    sl_b = features_b["sentence_length"]
    mean_sim = 1.0 - min(abs(sl_a["mean"] - sl_b["mean"]) / 20.0, 1.0)
    stdev_sim = 1.0 - min(abs(sl_a["stdev"] - sl_b["stdev"]) / 10.0, 1.0)
    dist_a = sl_a["distribution"]
    dist_b = sl_b["distribution"]
    dist_diff = sum(abs(dist_a[k] - dist_b[k]) for k in dist_a) / 4.0
    dist_sim = 1.0 - min(dist_diff, 1.0)
    dimension_scores["sentence_length"] = {
        "score": round((mean_sim * 0.4 + stdev_sim * 0.3 + dist_sim * 0.3), 4),
        "weight": 0.20,
    }

    # 2. Vocabulary richness similarity (weight: 0.15)
    va = features_a["vocabulary"]
    vb = features_b["vocabulary"]
    ttr_sim = 1.0 - min(abs(va["ttr"] - vb["ttr"]) / 0.3, 1.0)
    hapax_sim = 1.0 - min(abs(va["hapax_ratio"] - vb["hapax_ratio"]) / 0.3, 1.0)
    dimension_scores["vocabulary"] = {
        "score": round((ttr_sim * 0.5 + hapax_sim * 0.5), 4),
        "weight": 0.15,
    }

    # 3. Formality match (weight: 0.15)
    fa = features_a["formality"]["score"]
    fb = features_b["formality"]["score"]
    form_sim = 1.0 - min(abs(fa - fb) / 0.5, 1.0)
    dimension_scores["formality"] = {"score": round(form_sim, 4), "weight": 0.15}

    # 4. Punctuation profile (weight: 0.15)
    pa = features_a["punctuation"]
    pb = features_b["punctuation"]
    punct_diffs = []
    for k in pa:
        diff = abs(pa[k] - pb[k])
        normalized = 1.0 - min(diff / 0.5, 1.0)
        punct_diffs.append(normalized)
    dimension_scores["punctuation"] = {
        "score": round(statistics.mean(punct_diffs), 4),
        "weight": 0.15,
    }

    # 5. Rhetoric patterns (weight: 0.10)
    ra = features_a["rhetoric"]
    rb = features_b["rhetoric"]
    trans_sim = 1.0 - min(abs(ra["transition_rate"] - rb["transition_rate"]) / 1.0, 1.0)
    refl_sim = 1.0 - min(abs(ra["reflective_rate"] - rb["reflective_rate"]) / 1.0, 1.0)
    dimension_scores["rhetoric"] = {
        "score": round((trans_sim * 0.5 + refl_sim * 0.5), 4),
        "weight": 0.10,
    }

    # 6. Sensory language profile (weight: 0.10)
    sa = features_a["sensory_profile"]
    sb = features_b["sensory_profile"]
    sensory_sims = []
    for cat in sa:
        diff = abs(sa[cat] - sb[cat])
        sensory_sims.append(1.0 - min(diff / 0.02, 1.0))
    dimension_scores["sensory_profile"] = {
        "score": round(statistics.mean(sensory_sims), 4),
        "weight": 0.10,
    }

    # 7. Dialogue and first-person usage (weight: 0.10)
    dial_sim = 1.0 - min(abs(features_a["dialogue_ratio"] - features_b["dialogue_ratio"]) / 0.3, 1.0)
    fp_sim = 1.0 - min(abs(features_a["first_person_rate"] - features_b["first_person_rate"]) / 0.05, 1.0)
    dimension_scores["voice_markers"] = {
        "score": round((dial_sim * 0.4 + fp_sim * 0.6), 4),
        "weight": 0.10,
    }

    # 8. Paragraph structure (weight: 0.05)
    pma = features_a["paragraph"]["mean_length"]
    pmb = features_b["paragraph"]["mean_length"]
    para_sim = 1.0 - min(abs(pma - pmb) / 100.0, 1.0)
    dimension_scores["paragraph_structure"] = {
        "score": round(para_sim, 4),
        "weight": 0.05,
    }

    # Compute weighted total
    total_score = sum(d["score"] * d["weight"] for d in dimension_scores.values())
    total_weight = sum(d["weight"] for d in dimension_scores.values())
    final_score = total_score / total_weight if total_weight > 0 else 0.0

    return {
        "score": round(final_score, 4),
        "breakdown": dimension_scores,
    }


# ---------------------------------------------------------------------------
# Voice Profile Management
# ---------------------------------------------------------------------------

def create_voice_profile(texts: list[str], name: str = "default") -> dict:
    """
    Create a reference voice profile from multiple text samples.
    Averages features across samples to create a stable baseline.
    """
    all_features = [extract_features(t) for t in texts]
    valid = [f for f in all_features if "error" not in f]

    if not valid:
        return {"error": "No valid texts provided"}

    # Average numeric features
    def avg_nested(feature_list: list[dict], path: list[str]) -> float:
        values = []
        for f in feature_list:
            v = f
            for key in path:
                v = v.get(key, {}) if isinstance(v, dict) else 0
            if isinstance(v, (int, float)):
                values.append(v)
        return round(statistics.mean(values), 5) if values else 0.0

    profile = {
        "name": name,
        "sample_count": len(valid),
        "sentence_length_mean": avg_nested(valid, ["sentence_length", "mean"]),
        "sentence_length_stdev": avg_nested(valid, ["sentence_length", "stdev"]),
        "vocabulary_ttr": avg_nested(valid, ["vocabulary", "ttr"]),
        "vocabulary_hapax": avg_nested(valid, ["vocabulary", "hapax_ratio"]),
        "formality_score": avg_nested(valid, ["formality", "score"]),
        "contraction_rate": avg_nested(valid, ["formality", "contraction_rate"]),
        "transition_rate": avg_nested(valid, ["rhetoric", "transition_rate"]),
        "reflective_rate": avg_nested(valid, ["rhetoric", "reflective_rate"]),
        "dialogue_ratio": avg_nested(valid, ["dialogue_ratio"]),
        "first_person_rate": avg_nested(valid, ["first_person_rate"]),
        "em_dash_rate": avg_nested(valid, ["punctuation", "em_dash"]),
        "question_rate": avg_nested(valid, ["punctuation", "question"]),
    }

    # Store full averaged features for comparison
    profile["_full_features"] = valid[0]  # Use first as template structure

    return profile


def save_voice_profile(profile: dict, path: Path) -> None:
    """Save a voice profile to JSON."""
    path.write_text(json.dumps(profile, indent=2))


def load_voice_profile(path: Path) -> dict:
    """Load a voice profile from JSON."""
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def format_comparison_report(
    file_a: str, file_b: str, features_a: dict, features_b: dict,
    similarity: dict, threshold: float
) -> str:
    """Format a human-readable comparison report."""
    lines = []
    score = similarity["score"]
    status = "PASS" if score >= threshold else "FAIL"

    lines.append("=" * 68)
    lines.append("  VOICE CONSISTENCY CHECK")
    lines.append("=" * 68)
    lines.append(f"  File A: {file_a}")
    lines.append(f"  File B: {file_b}")
    lines.append(f"  Similarity: {score:.4f}  |  Threshold: {threshold:.2f}  |  [{status}]")
    lines.append("")

    lines.append("  Dimension Breakdown:")
    for dim, data in sorted(similarity["breakdown"].items()):
        bar_len = int(data["score"] * 30)
        bar = "#" * bar_len + "." * (30 - bar_len)
        lines.append(f"    {dim:25s} [{bar}] {data['score']:.3f} (w={data['weight']:.2f})")
    lines.append("")

    # Side-by-side key metrics
    lines.append("  Key Metrics Comparison:")
    lines.append(f"    {'Metric':30s} {'File A':>10s} {'File B':>10s} {'Delta':>10s}")
    lines.append("    " + "-" * 62)

    comparisons = [
        ("Sentence length (mean)", features_a.get("sentence_length", {}).get("mean", 0),
         features_b.get("sentence_length", {}).get("mean", 0)),
        ("Sentence length (stdev)", features_a.get("sentence_length", {}).get("stdev", 0),
         features_b.get("sentence_length", {}).get("stdev", 0)),
        ("Vocabulary TTR", features_a.get("vocabulary", {}).get("ttr", 0),
         features_b.get("vocabulary", {}).get("ttr", 0)),
        ("Formality score", features_a.get("formality", {}).get("score", 0),
         features_b.get("formality", {}).get("score", 0)),
        ("First-person rate", features_a.get("first_person_rate", 0),
         features_b.get("first_person_rate", 0)),
        ("Dialogue ratio", features_a.get("dialogue_ratio", 0),
         features_b.get("dialogue_ratio", 0)),
        ("Transition rate", features_a.get("rhetoric", {}).get("transition_rate", 0),
         features_b.get("rhetoric", {}).get("transition_rate", 0)),
        ("Reflective rate", features_a.get("rhetoric", {}).get("reflective_rate", 0),
         features_b.get("rhetoric", {}).get("reflective_rate", 0)),
    ]
    for label, va, vb in comparisons:
        delta = vb - va
        lines.append(f"    {label:30s} {va:10.4f} {vb:10.4f} {delta:+10.4f}")

    lines.append("")
    if score < threshold:
        lines.append(f"  WARNING: Voice consistency below threshold ({score:.3f} < {threshold:.2f})")
        # Identify weakest dimensions
        sorted_dims = sorted(
            similarity["breakdown"].items(), key=lambda x: x[1]["score"]
        )
        lines.append(f"  Weakest dimensions:")
        for dim, data in sorted_dims[:3]:
            lines.append(f"    - {dim}: {data['score']:.3f}")
    lines.append("=" * 68)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Multi-Chapter Analysis
# ---------------------------------------------------------------------------

def analyze_directory(directory: Path, threshold: float) -> dict:
    """
    Analyze all .md and .txt files in a directory for voice consistency.
    Returns pairwise comparison matrix and overall consistency score.
    """
    files = sorted(
        list(directory.glob("*.md")) + list(directory.glob("*.txt"))
    )
    if len(files) < 2:
        return {"error": f"Need at least 2 files, found {len(files)}"}

    print(f"Analyzing {len(files)} files in {directory}...")
    features = {}
    for f in files:
        text = f.read_text()
        features[f.name] = extract_features(text)

    # Pairwise comparison
    comparisons = []
    scores = []
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            name_a = files[i].name
            name_b = files[j].name
            sim = compute_similarity(features[name_a], features[name_b])
            comparisons.append({
                "file_a": name_a,
                "file_b": name_b,
                "score": sim["score"],
                "passed": sim["score"] >= threshold,
            })
            scores.append(sim["score"])

    # Find outliers (files most dissimilar to the group)
    file_avg_scores = {}
    for f in files:
        related = [c for c in comparisons if f.name in (c["file_a"], c["file_b"])]
        file_avg_scores[f.name] = statistics.mean([c["score"] for c in related])

    sorted_files = sorted(file_avg_scores.items(), key=lambda x: x[1])
    outliers = [f for f, s in sorted_files if s < threshold]

    return {
        "file_count": len(files),
        "comparison_count": len(comparisons),
        "overall_consistency": round(statistics.mean(scores), 4) if scores else 0.0,
        "min_pair_score": round(min(scores), 4) if scores else 0.0,
        "max_pair_score": round(max(scores), 4) if scores else 0.0,
        "threshold": threshold,
        "all_passed": all(c["passed"] for c in comparisons),
        "failing_pairs": [c for c in comparisons if not c["passed"]],
        "outlier_files": outliers,
        "pairwise": comparisons,
        "file_average_scores": {k: round(v, 4) for k, v in file_avg_scores.items()},
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Voice Consistency Checker")
    parser.add_argument("files", nargs="*", help="Text files to compare (2 for pairwise)")
    parser.add_argument("--directory", "-d", type=str, help="Directory of chapters to analyze")
    parser.add_argument("--reference", "-r", type=str, help="Reference voice profile JSON")
    parser.add_argument("--threshold", "-t", type=float, default=0.65,
                        help="Minimum similarity threshold (default: 0.65)")
    parser.add_argument("--output-profile", type=str,
                        help="Save extracted voice profile to JSON")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Mode 1: Directory analysis
    if args.directory:
        dirpath = Path(args.directory)
        if not dirpath.is_dir():
            print(f"[ERROR] Not a directory: {args.directory}")
            sys.exit(1)

        result = analyze_directory(dirpath, args.threshold)
        if "error" in result:
            print(f"[ERROR] {result['error']}")
            sys.exit(1)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nVoice Consistency Report for {args.directory}")
            print("=" * 60)
            print(f"Files analyzed: {result['file_count']}")
            print(f"Overall consistency: {result['overall_consistency']:.4f}")
            print(f"Score range: {result['min_pair_score']:.4f} - {result['max_pair_score']:.4f}")
            print(f"Threshold: {result['threshold']:.2f}")
            print(f"Status: {'PASS' if result['all_passed'] else 'FAIL'}")
            if result["failing_pairs"]:
                print(f"\nFailing pairs:")
                for fp in result["failing_pairs"]:
                    print(f"  {fp['file_a']} <-> {fp['file_b']}: {fp['score']:.4f}")
            if result["outlier_files"]:
                print(f"\nOutlier files (below threshold):")
                for o in result["outlier_files"]:
                    print(f"  {o}: avg score {result['file_average_scores'][o]:.4f}")
            print()
            print("Pairwise scores:")
            for c in result["pairwise"]:
                mark = "OK" if c["passed"] else "XX"
                print(f"  [{mark}] {c['file_a']:30s} <-> {c['file_b']:30s} : {c['score']:.4f}")

        sys.exit(0 if result["all_passed"] else 1)

    # Mode 2: Two-file comparison
    if len(args.files) >= 2:
        path_a = Path(args.files[0])
        path_b = Path(args.files[1])
        if not path_a.exists() or not path_b.exists():
            print(f"[ERROR] File not found")
            sys.exit(1)

        text_a = path_a.read_text()
        text_b = path_b.read_text()
        features_a = extract_features(text_a)
        features_b = extract_features(text_b)
        similarity = compute_similarity(features_a, features_b)

        if args.json:
            output = {
                "file_a": str(path_a),
                "file_b": str(path_b),
                "features_a": features_a,
                "features_b": features_b,
                "similarity": similarity,
                "threshold": args.threshold,
                "passed": similarity["score"] >= args.threshold,
            }
            print(json.dumps(output, indent=2))
        else:
            report = format_comparison_report(
                str(path_a), str(path_b), features_a, features_b,
                similarity, args.threshold,
            )
            print(report)

        # Save profile if requested
        if args.output_profile:
            profile = create_voice_profile([text_a, text_b], name=path_a.stem)
            save_voice_profile(profile, Path(args.output_profile))
            print(f"Voice profile saved: {args.output_profile}")

        sys.exit(0 if similarity["score"] >= args.threshold else 1)

    # Mode 3: Single file feature extraction
    if len(args.files) == 1:
        path = Path(args.files[0])
        if not path.exists():
            print(f"[ERROR] File not found: {path}")
            sys.exit(1)

        text = path.read_text()
        features = extract_features(text)

        if args.output_profile:
            profile = create_voice_profile([text], name=path.stem)
            save_voice_profile(profile, Path(args.output_profile))
            print(f"Voice profile saved: {args.output_profile}")

        if args.json:
            print(json.dumps(features, indent=2))
        else:
            print(f"\nVoice Features for {path.name}")
            print("=" * 50)
            print(json.dumps(features, indent=2))

        sys.exit(0)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
