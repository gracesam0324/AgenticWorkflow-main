#!/usr/bin/env python3
"""
P1 Validation: Content Insertion Accuracy.

Verifies that SOT content (quiz questions, schedule, lyrics, team names)
appears verbatim in generated HTML files.

H-CRITICAL — deterministic string matching.

Usage:
    python3 validate_content_insertion.py --project-dir . [--json]

Output (JSON):
    {"match_rate": 0.95, "total_in_sot": 20, "found_in_html": 19,
     "missing": ["Question 15 text..."], "extra": []}

SOT: Read-only.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def read_sot(project_dir):
    """Read app-state.json (SOT)."""
    sot_path = os.path.join(project_dir, "app-state.json")
    if not os.path.exists(sot_path):
        return None
    try:
        with open(sot_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def read_html(project_dir):
    """Read all HTML files concatenated."""
    content = ""
    for root, _dirs, files in os.walk(project_dir):
        if any(skip in root for skip in ["node_modules", ".git", "scripts"]):
            continue
        for f in files:
            if f.endswith(".html"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                        content += fh.read() + "\n"
                except (UnicodeDecodeError, OSError):
                    pass
    return content


def normalize_text(text):
    """Normalize whitespace for comparison."""
    if not isinstance(text, str):
        return str(text)
    return re.sub(r'\s+', ' ', text.strip())


def extract_content_items(sot):
    """Extract content items from SOT based on app type."""
    items = []
    content = sot.get("content", {})
    intent = sot.get("intent", {})
    app_type = intent.get("app_type", "")

    # Team names (common across quiz, score, combined)
    team_names = intent.get("team_names", []) or content.get("team_names", [])
    for name in team_names:
        if name:
            items.append({"type": "team_name", "text": name})

    # Quiz questions
    questions = content.get("quiz_questions", [])
    for q in questions:
        if isinstance(q, dict):
            if q.get("question"):
                items.append({"type": "quiz_question", "text": q["question"]})
            if q.get("answer"):
                items.append({"type": "quiz_answer", "text": q["answer"]})
        elif isinstance(q, str) and q:
            items.append({"type": "quiz_question", "text": q})

    # Schedule items
    schedule = content.get("schedule", [])
    for s in schedule:
        if isinstance(s, dict):
            if s.get("title"):
                items.append({"type": "schedule_title", "text": s["title"]})
        elif isinstance(s, str) and s:
            items.append({"type": "schedule_item", "text": s})

    # Lyrics
    lyrics = content.get("lyrics", [])
    for l in lyrics:
        if isinstance(l, dict):
            if l.get("song_title"):
                items.append({"type": "song_title", "text": l["song_title"]})
        elif isinstance(l, str) and l:
            items.append({"type": "lyric", "text": l})

    # Missions (stamp rally)
    missions = content.get("missions", [])
    for m in missions:
        if isinstance(m, dict):
            if m.get("name"):
                items.append({"type": "mission_name", "text": m["name"]})
        elif isinstance(m, str) and m:
            items.append({"type": "mission", "text": m})

    # Bible passages (QT)
    passages = content.get("bible_passages", [])
    for p in passages:
        if isinstance(p, dict):
            if p.get("reference"):
                items.append({"type": "bible_ref", "text": p["reference"]})
        elif isinstance(p, str) and p:
            items.append({"type": "bible_passage", "text": p})

    return items


def check_content(project_dir):
    """Check SOT content appears in HTML."""
    sot = read_sot(project_dir)
    if not sot:
        return {
            "match_rate": 0,
            "total_in_sot": 0,
            "found_in_html": 0,
            "missing": [],
            "extra": [],
            "pass": False,
            "detail": "app-state.json not found or invalid"
        }

    html = read_html(project_dir)
    if not html:
        return {
            "match_rate": 0,
            "total_in_sot": 0,
            "found_in_html": 0,
            "missing": [],
            "extra": [],
            "pass": False,
            "detail": "No HTML files found"
        }

    items = extract_content_items(sot)
    if not items:
        return {
            "match_rate": 1.0,
            "total_in_sot": 0,
            "found_in_html": 0,
            "missing": [],
            "extra": [],
            "pass": True,
            "detail": "No content items to verify"
        }

    html_normalized = normalize_text(html)
    found = []
    missing = []

    for item in items:
        text_normalized = normalize_text(item["text"])
        if text_normalized in html_normalized:
            found.append(item)
        else:
            missing.append(item)

    total = len(items)
    found_count = len(found)
    match_rate = found_count / total if total > 0 else 1.0

    return {
        "match_rate": round(match_rate, 4),
        "total_in_sot": total,
        "found_in_html": found_count,
        "missing": [{"type": m["type"], "text": m["text"][:80]} for m in missing],
        "extra": [],
        "pass": match_rate >= 0.95,
        "value": match_rate,
        "threshold": 0.95,
        "detail": f"Match rate: {match_rate:.1%} ({found_count}/{total})"
    }


def main():
    parser = argparse.ArgumentParser(description="Validate content insertion accuracy")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"Directory not found: {project_dir}"}))
        sys.exit(1)

    result = check_content(project_dir)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["pass"] else "FAIL"
        print(f"Content insertion: {status} — {result['detail']}")
        if result["missing"]:
            print(f"Missing items:")
            for m in result["missing"][:10]:
                print(f"  [{m['type']}] {m['text']}")


if __name__ == "__main__":
    main()
