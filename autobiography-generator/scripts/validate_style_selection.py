#!/usr/bin/env python3
"""validate_style_selection.py — Deterministic style selection integrity check.

Checks SS1-SS5:
  SS1: style_selection.json exists and is valid JSON
  SS2: selected_style is one of 10 known styles or "custom"
  SS3: blending_ratio in range 0.0-1.0
  SS4: 3 calibration sample files exist, each >= 400 words
  SS5: story_bible.voice_guide has been updated with blended parameters

Usage:
  python3 scripts/validate_style_selection.py --project-dir .

100% deterministic. Zero AI calls.
"""

import argparse
import json
import os
import sys


VALID_STYLES = [
    "hemingway", "shakespeare", "hesse", "kant", "marquez",
    "austen", "dostoevsky", "woolf", "orwell", "murakami",
    "custom",
]


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def validate(project_dir: str) -> dict:
    result = {"valid": True, "checks": {}, "errors": [], "warnings": []}

    # SS1: style_selection.json exists and loads
    sel_path = os.path.join(project_dir, "outputs", "style-selection", "style_selection.json")
    sel = _load_json(sel_path)
    if not sel:
        result["valid"] = False
        result["checks"]["SS1"] = "FAIL"
        result["errors"].append(f"SS1: style_selection.json not found at {sel_path}")
        return result
    result["checks"]["SS1"] = "PASS"

    # SS2: selected_style is valid
    style = sel.get("selected_style", "")
    if style not in VALID_STYLES:
        result["valid"] = False
        result["checks"]["SS2"] = "FAIL"
        result["errors"].append(f"SS2: Unknown style '{style}'. Valid: {VALID_STYLES}")
    else:
        result["checks"]["SS2"] = "PASS"

    # SS3: blending_ratio in range
    ratio = sel.get("blending_ratio")
    if not isinstance(ratio, (int, float)) or ratio < 0.0 or ratio > 1.0:
        result["valid"] = False
        result["checks"]["SS3"] = "FAIL"
        result["errors"].append(f"SS3: blending_ratio {ratio} not in range [0.0, 1.0]")
    else:
        result["checks"]["SS3"] = "PASS"

    # SS4: 3 calibration samples exist, each >= 400 words
    sel_dir = os.path.join(project_dir, "outputs", "style-selection")
    sample_files = []
    for suffix in ["_v1.md", "_v2.md", "_v3.md", "_vA.md", "_vB.md", "_vC.md",
                    "calibration_v1.md", "calibration_v2.md", "calibration_v3.md",
                    "calibration_vA.md", "calibration_vB.md", "calibration_vC.md"]:
        candidate = os.path.join(sel_dir, f"calibration{suffix}" if not suffix.startswith("calibration") else suffix)
        if os.path.isfile(candidate):
            sample_files.append(candidate)

    # Also check for any .md files in the directory
    if len(sample_files) < 3 and os.path.isdir(sel_dir):
        md_files = sorted([
            os.path.join(sel_dir, f) for f in os.listdir(sel_dir)
            if f.endswith(".md") and not f.endswith(".ko.md")
        ])
        sample_files = list(set(sample_files + md_files))[:3]

    if len(sample_files) < 3:
        result["valid"] = False
        result["checks"]["SS4"] = "FAIL"
        result["errors"].append(f"SS4: Found {len(sample_files)} calibration samples, need 3")
    else:
        short_samples = []
        for sf in sample_files[:3]:
            with open(sf, "r", encoding="utf-8") as f:
                wc = len(f.read().split())
            if wc < 400:
                short_samples.append(f"{os.path.basename(sf)}: {wc} words")
        if short_samples:
            result["valid"] = False
            result["checks"]["SS4"] = "FAIL"
            result["errors"].append(f"SS4: Samples under 400 words: {short_samples}")
        else:
            result["checks"]["SS4"] = "PASS"

    # SS5: story_bible.voice_guide updated
    sb_path = os.path.join(project_dir, "outputs", "story-bible", "story_bible.json")
    sb = _load_json(sb_path)
    if not sb or "voice_guide" not in sb:
        result["valid"] = False
        result["checks"]["SS5"] = "FAIL"
        result["errors"].append("SS5: story_bible.voice_guide not found")
    else:
        vg = sb["voice_guide"]
        metadata = vg.get("_blend_metadata", {})
        if metadata.get("computed_by") == "style_blender.py":
            result["checks"]["SS5"] = "PASS"
        else:
            result["valid"] = False
            result["checks"]["SS5"] = "FAIL"
            result["errors"].append("SS5: voice_guide not updated by style_blender.py")

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate style selection (SS1-SS5)")
    parser.add_argument("--project-dir", required=True)
    args = parser.parse_args()

    result = validate(args.project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
