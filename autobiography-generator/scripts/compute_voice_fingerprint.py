#!/usr/bin/env python3
"""compute_voice_fingerprint.py — Deterministic voice parameter extraction from interviews.

Computes 12 quantitative voice parameters directly from interview transcript text.
This REPLACES AI estimation — all values are computed by Python.

Output: outputs/voice_fingerprint.json

Usage:
  python3 scripts/compute_voice_fingerprint.py --project-dir .

100% deterministic. Zero AI calls. Zero network calls.
"""

import argparse
import json
import hashlib
import math
import os
import re
import sys
from collections import Counter


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _extract_all_text(project_dir: str) -> str:
    """Extract all interview content as a single text blob."""
    interviews_dir = os.path.join(project_dir, "outputs", "interviews")
    if not os.path.isdir(interviews_dir):
        return ""

    texts = []
    for fname in sorted(os.listdir(interviews_dir)):
        if not fname.startswith("INT-") or not fname.endswith(".json"):
            continue
        data = _load_json(os.path.join(interviews_dir, fname))
        if not data or "segments" not in data:
            continue
        for seg in data["segments"]:
            content = seg.get("content", "")
            if isinstance(content, str):
                texts.append(content)
    return "\n".join(texts)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using common delimiters."""
    # Handle Korean and English sentence boundaries
    sentences = re.split(r'(?<=[.!?。])\s+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 2]


def _count_words(text: str) -> int:
    """Count words (handles both English and Korean mixed text)."""
    # For Korean: each character cluster counts; for English: space-separated
    return len(text.split())


def _is_dialogue(line: str) -> bool:
    """Check if a line contains direct speech."""
    patterns = [
        r'"[^"]{5,}"',           # English double quotes
        r"'[^']{5,}'",           # English single quotes
        r'"[^"]{5,}"',           # Smart quotes
        r'「[^」]{3,}」',          # Korean quotation
        r'"[^"]{3,}"',           # Korean double quotes
    ]
    return any(re.search(p, line) for p in patterns)


def _is_passive(sentence: str) -> bool:
    """Detect passive voice patterns (English + Korean)."""
    en_passive = re.search(
        r'\b(was|were|is|are|been|being|be)\s+\w+ed\b',
        sentence, re.IGNORECASE
    )
    ko_passive = re.search(
        r'(되었|되어|되는|받았|받는|당했|당하)',
        sentence
    )
    return bool(en_passive or ko_passive)


def _count_adverbs(text: str) -> int:
    """Count adverbs (English -ly words + common Korean adverbs)."""
    en_adverbs = len(re.findall(r'\b\w+ly\b', text, re.IGNORECASE))
    ko_adverbs = len(re.findall(
        r'(매우|정말|아주|너무|상당히|꽤|참|진짜|완전히|절대로|반드시|대단히)',
        text
    ))
    return en_adverbs + ko_adverbs


def _extract_repeated_phrases(text: str, min_count: int = 3) -> list[str]:
    """Find phrases (2-4 words) that appear at least min_count times."""
    words = text.lower().split()
    phrases = Counter()
    for n in range(2, 5):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i+n])
            if len(phrase) > 5:  # skip very short
                phrases[phrase] += 1

    return [p for p, c in phrases.most_common(20) if c >= min_count]


def _compute_vocabulary_tier(words: list[str]) -> str:
    """Classify vocabulary level based on unique-to-total ratio and word length."""
    if not words:
        return "unknown"
    unique_ratio = len(set(words)) / len(words)
    avg_word_len = sum(len(w) for w in words) / len(words)

    if unique_ratio > 0.65 and avg_word_len > 5.5:
        return "advanced"
    elif unique_ratio > 0.50 and avg_word_len > 4.5:
        return "intermediate"
    else:
        return "basic"


def compute(project_dir: str) -> dict:
    """Compute all 12 voice parameters from interview transcripts."""
    text = _extract_all_text(project_dir)
    if not text:
        return {"error": "No interview text found", "parameters": {}}

    sentences = _split_sentences(text)
    words = text.split()
    total_words = len(words)

    if not sentences or total_words == 0:
        return {"error": "Insufficient text for analysis", "parameters": {}}

    # 1. avg_sentence_length
    sent_lengths = [_count_words(s) for s in sentences]
    avg_sent_len = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0

    # 2. sentence_length_std
    if len(sent_lengths) > 1:
        mean = avg_sent_len
        variance = sum((x - mean) ** 2 for x in sent_lengths) / (len(sent_lengths) - 1)
        sent_len_std = math.sqrt(variance)
    else:
        sent_len_std = 0

    # 3. dialogue_ratio
    dialogue_lines = sum(1 for s in sentences if _is_dialogue(s))
    dialogue_ratio = dialogue_lines / len(sentences) if sentences else 0

    # 4. passive_voice_pct
    passive_count = sum(1 for s in sentences if _is_passive(s))
    passive_pct = (passive_count / len(sentences)) * 100 if sentences else 0

    # 5. adverb_density
    adverb_count = _count_adverbs(text)
    adverb_density = adverb_count / total_words if total_words else 0

    # 6. unique_word_ratio
    unique_ratio = len(set(w.lower() for w in words)) / total_words if total_words else 0

    # 7. avg_paragraph_length (split by double newlines)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    para_lengths = [_count_words(p) for p in paragraphs]
    avg_para_len = sum(para_lengths) / len(para_lengths) if para_lengths else 0

    # 8. exclamation_ratio
    excl_count = sum(1 for s in sentences if s.rstrip().endswith("!"))
    excl_ratio = excl_count / len(sentences) if sentences else 0

    # 9. question_ratio
    q_count = sum(1 for s in sentences if s.rstrip().endswith("?"))
    q_ratio = q_count / len(sentences) if sentences else 0

    # 10. vocabulary_level
    vocab_level = _compute_vocabulary_tier(words)

    # 11. favorite_expressions (repeated phrases)
    favorite_exprs = _extract_repeated_phrases(text, min_count=3)

    # 12. max_sentence_length
    max_sent_len = max(sent_lengths) if sent_lengths else 0

    # Compute provenance hash from input text (tamper detection)
    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    return {
        "source": "compute_voice_fingerprint.py",
        "method": "deterministic_python",
        "source_hash": source_hash,
        "total_words_analyzed": total_words,
        "total_sentences_analyzed": len(sentences),
        "total_interviews_analyzed": len([
            f for f in os.listdir(os.path.join(project_dir, "outputs", "interviews"))
            if f.startswith("INT-") and f.endswith(".json")
        ]) if os.path.isdir(os.path.join(project_dir, "outputs", "interviews")) else 0,
        "parameters": {
            "avg_sentence_length": round(avg_sent_len, 1),
            "sentence_length_std": round(sent_len_std, 1),
            "max_sentence_length": max_sent_len,
            "dialogue_ratio": round(dialogue_ratio, 3),
            "passive_voice_pct": round(passive_pct, 1),
            "adverb_density": round(adverb_density, 4),
            "unique_word_ratio": round(unique_ratio, 3),
            "avg_paragraph_length": round(avg_para_len, 1),
            "exclamation_ratio": round(excl_ratio, 3),
            "question_ratio": round(q_ratio, 3),
            "vocabulary_level": vocab_level,
            "favorite_expressions": favorite_exprs[:10],
            "sentence_length_distribution": {
                "short_pct": round(sum(1 for l in sent_lengths if l <= 10) / len(sent_lengths) * 100, 1) if sent_lengths else 0,
                "medium_pct": round(sum(1 for l in sent_lengths if 11 <= l <= 20) / len(sent_lengths) * 100, 1) if sent_lengths else 0,
                "long_pct": round(sum(1 for l in sent_lengths if l > 20) / len(sent_lengths) * 100, 1) if sent_lengths else 0,
            }
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Compute voice fingerprint from interviews")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    args = parser.parse_args()

    result = compute(args.project_dir)
    output_path = os.path.join(args.project_dir, "outputs", "voice_fingerprint.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if "error" not in result else 1)


if __name__ == "__main__":
    main()
