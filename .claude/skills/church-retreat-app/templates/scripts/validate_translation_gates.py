#!/usr/bin/env python3
"""
P1 Validation: Translation Gates T1-T3.

T1: .ko files exist for all phase reports.
T2: pACS >= 70 for each translation.
T3: Glossary consistency.

H-CRITICAL — deterministic file/text checks.

Usage:
    python3 validate_translation_gates.py --project-dir . [--json]

Output (JSON): {"T1": {"pass": true, ...}, "T2": {"pass": true, ...}, "T3": {"pass": true, ...}}
SOT: Read-only.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ── Configuration ──
GLOSSARY_PATHS = [
    "translations/glossary.yaml",
    "translations/church-app-glossary.yaml",
]


def check_t1(project_dir):
    """T1: .ko files exist for all phase reports."""
    reports_dir = os.path.join(project_dir, "reports")
    if not os.path.isdir(reports_dir):
        return {
            "pass": False,
            "value": {"reports_dir_exists": False},
            "threshold": "all phases have .ko files",
            "detail": "reports/ directory not found"
        }

    # Find all English phase reports
    english_reports = []
    ko_reports = []
    for f in os.listdir(reports_dir):
        if f.endswith(".ko.md"):
            ko_reports.append(f)
        elif f.endswith(".md") and re.match(r'phase\d+', f):
            english_reports.append(f)

    # Check each English report has a .ko pair
    missing = []
    for eng in english_reports:
        ko_name = eng.replace(".md", ".ko.md")
        if ko_name not in ko_reports:
            missing.append(ko_name)

    return {
        "pass": len(missing) == 0 and len(english_reports) > 0,
        "value": {"english": len(english_reports), "korean": len(ko_reports),
                  "missing": missing},
        "threshold": "all phases",
        "detail": f"{len(ko_reports)}/{len(english_reports)} .ko files" +
                  (f", missing: {missing}" if missing else "")
    }


def check_t2(project_dir):
    """T2: pACS >= 70 for each translation."""
    pacs_dir = os.path.join(project_dir, "pacs-logs")
    if not os.path.isdir(pacs_dir):
        return {
            "pass": False,
            "value": {"pacs_dir_exists": False},
            "threshold": "pACS >= 70",
            "detail": "pacs-logs/ directory not found"
        }

    scores = {}
    below_70 = []
    for f in os.listdir(pacs_dir):
        if "translation" in f and f.endswith(".md"):
            filepath = os.path.join(pacs_dir, f)
            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    content = fh.read()
                match = re.search(r'pACS\s*=\s*(\d+)', content)
                if match:
                    score = int(match.group(1))
                    scores[f] = score
                    if score < 70:
                        below_70.append({"file": f, "score": score})
            except OSError:
                below_70.append({"file": f, "score": "unreadable"})

    return {
        "pass": len(below_70) == 0 and len(scores) > 0,
        "value": {"scores": scores, "below_70": below_70},
        "threshold": 70,
        "detail": f"{len(scores)} translation(s) scored" +
                  (f", {len(below_70)} below 70" if below_70 else ", all >= 70")
    }


def check_t3(project_dir):
    """T3: Glossary consistency — terms correctly translated in .ko files."""
    # Load glossary
    glossary = {}
    base_dir = project_dir

    # Try to find glossary files (may be in parent AgenticWorkflow dir)
    for rel_path in GLOSSARY_PATHS:
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            # Try parent directories
            parent = os.path.dirname(base_dir)
            full_path = os.path.join(parent, rel_path)
        if os.path.exists(full_path):
            try:
                # M-3 FIX: Use yaml library if available, fallback to improved regex
                try:
                    import yaml
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        terms = data.get("terms", data)
                        if isinstance(terms, dict):
                            glossary.update(terms)
                except ImportError:
                    # Fallback: improved regex handles indented key: value under terms:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    in_terms = False
                    for line in content.split("\n"):
                        if line.strip() == "terms:":
                            in_terms = True
                            continue
                        if in_terms and line.strip() and not line.startswith(" "):
                            in_terms = False
                        if in_terms:
                            match = re.match(r'\s+(.+?):\s+(.+)', line)
                            if match:
                                glossary[match.group(1).strip()] = match.group(2).strip()
            except OSError:
                pass

    if not glossary:
        return {
            "pass": True,
            "value": {"glossary_terms": 0},
            "threshold": "consistency",
            "detail": "No glossary found (skipping T3)"
        }

    # Check .ko files for glossary consistency
    reports_dir = os.path.join(project_dir, "reports")
    inconsistencies = []

    if os.path.isdir(reports_dir):
        for f in os.listdir(reports_dir):
            if f.endswith(".ko.md"):
                filepath = os.path.join(reports_dir, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        ko_content = fh.read()
                    for eng_term, kor_term in glossary.items():
                        # If English term appears but Korean term doesn't, inconsistency
                        if eng_term.lower() in ko_content.lower() and kor_term not in ko_content:
                            inconsistencies.append({
                                "file": f, "english": eng_term,
                                "expected_korean": kor_term
                            })
                except OSError:
                    pass

    return {
        "pass": len(inconsistencies) == 0,
        "value": {"glossary_terms": len(glossary),
                  "inconsistencies": inconsistencies[:10]},
        "threshold": 0,
        "detail": f"{len(glossary)} glossary terms, "
                  f"{len(inconsistencies)} inconsistenc(ies)"
    }


def main():
    parser = argparse.ArgumentParser(description="Validate translation gates T1-T3")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"Directory not found: {project_dir}"}))
        sys.exit(1)

    results = {
        "T1": check_t1(project_dir),
        "T2": check_t2(project_dir),
        "T3": check_t3(project_dir),
    }

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for name, result in results.items():
            status = "PASS" if result["pass"] else "FAIL"
            print(f"{name}: {status} — {result['detail']}")


if __name__ == "__main__":
    main()
