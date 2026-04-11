#!/usr/bin/env python3
"""style_blender.py — Pure arithmetic blending of style parameters + observed voice.

Blends writing style skill parameters with Python-computed voice fingerprint
using user-selected blending ratio. Zero AI involvement.

Modes:
  --apply:  Compute blended voice_guide and update story_bible.json
  --verify: Verify that story_bible.voice_guide matches expected blend

Usage:
  python3 scripts/style_blender.py --apply --project-dir .
  python3 scripts/style_blender.py --verify --project-dir .

100% deterministic. Zero AI calls.
"""

import argparse
import json
import os
import sys

import yaml


# Numeric parameters that can be arithmetically blended
NUMERIC_PARAMS = [
    "avg_sentence_length",
    "max_sentence_length",
    "dialogue_ratio",
    "passive_voice_max",
    "adverb_density_max",
    "show_dont_tell_ratio",
    "metaphor_density",
]


def _load_json(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _load_yaml(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        return None


def _parse_range(value) -> float:
    """Convert range strings like '8-12' to midpoint, or return float directly."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if "-" in value:
            parts = value.split("-")
            try:
                return (float(parts[0]) + float(parts[1])) / 2
            except (ValueError, IndexError):
                return 0.0
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _extract_skill_params(skill_path: str) -> dict:
    """Extract voice parameters from a SKILL.md file's YAML block."""
    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {}

    # Find YAML block within ```yaml ... ```
    import re
    match = re.search(r'```yaml\s*\n(.*?)```', content, re.DOTALL)
    if not match:
        return {}

    try:
        params_raw = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}

    if not isinstance(params_raw, dict):
        return {}

    # Flatten nested structure
    flat = {}
    for key, val in params_raw.items():
        if isinstance(val, dict):
            for subkey, subval in val.items():
                flat[f"{key}.{subkey}"] = subval
                flat[subkey] = subval
        else:
            flat[key] = val

    # Normalize to standard param names
    result = {}
    mapping = {
        "avg_words": "avg_sentence_length",
        "max_words": "max_sentence_length",
        "avg_sentences": "avg_paragraph_length",
    }
    for k, v in flat.items():
        canonical = mapping.get(k, k)
        result[canonical] = _parse_range(v)

    return result


def blend(skill_params: dict, observed_params: dict, ratio: float) -> dict:
    """Blend style parameters with observed voice parameters.

    Args:
        skill_params: Voice parameters from the selected writing style skill
        observed_params: Voice fingerprint computed from interviews (Python)
        ratio: 0.0 = 100% observed, 1.0 = 100% style skill

    Returns:
        Blended parameters dictionary
    """
    blended = {}

    for param in NUMERIC_PARAMS:
        skill_val = _parse_range(skill_params.get(param, 0))
        obs_val = _parse_range(observed_params.get(param, 0))

        if skill_val == 0 and obs_val == 0:
            continue

        # If one side is missing, use the other
        if skill_val == 0:
            blended[param] = round(obs_val, 3)
        elif obs_val == 0:
            blended[param] = round(skill_val, 3)
        else:
            blended[param] = round(skill_val * ratio + obs_val * (1 - ratio), 3)

    # Non-numeric: merge forbidden_words (union)
    skill_forbidden = set(skill_params.get("forbidden_words", []))
    obs_forbidden = set(observed_params.get("forbidden_words", []))
    blended["forbidden_words"] = sorted(skill_forbidden | obs_forbidden)

    # Non-numeric: merge favorite_expressions (from observed only)
    blended["favorite_expressions"] = observed_params.get("favorite_expressions", [])

    # Record blending metadata
    blended["_blend_metadata"] = {
        "selected_style": skill_params.get("_style_name", "unknown"),
        "blending_ratio": ratio,
        "method": "arithmetic_blend",
        "computed_by": "style_blender.py",
    }

    return blended


def apply_blend(project_dir: str) -> dict:
    """Load inputs, compute blend, update story_bible.voice_guide."""
    # Load style selection
    sel_path = os.path.join(project_dir, "outputs", "style-selection", "style_selection.json")
    selection = _load_json(sel_path)
    if not selection:
        return {"error": f"style_selection.json not found at {sel_path}"}

    style_name = selection.get("selected_style", "")
    ratio = selection.get("blending_ratio", 0.3)

    # Validate blending_ratio range (hallucination prevention — cannot be <0 or >1)
    if not isinstance(ratio, (int, float)) or ratio < 0.0 or ratio > 1.0:
        return {"error": f"blending_ratio {ratio} is outside valid range [0.0, 1.0]. Cannot proceed."}

    # Load skill parameters
    skill_path = os.path.join(
        project_dir, "..", ".claude", "skills", "writing-styles",
        f"style-{style_name}", "SKILL.md"
    )
    # Try alternate path
    if not os.path.isfile(skill_path):
        skill_path = os.path.join(
            os.path.dirname(os.path.dirname(project_dir)),
            ".claude", "skills", "writing-styles",
            f"style-{style_name}", "SKILL.md"
        )

    skill_params = _extract_skill_params(skill_path) if os.path.isfile(skill_path) else {}
    if not skill_params and style_name != "custom":
        return {"error": f"Skill parameters not found for style-{style_name}"}

    skill_params["_style_name"] = style_name

    # Load observed voice fingerprint (Python-computed)
    fp_path = os.path.join(project_dir, "outputs", "voice_fingerprint.json")
    fp = _load_json(fp_path)
    if not fp or "parameters" not in fp:
        return {"error": f"voice_fingerprint.json not found at {fp_path}"}

    observed = fp["parameters"]

    # Compute blend
    blended = blend(skill_params, observed, ratio)

    # Update story_bible.voice_guide
    sb_path = os.path.join(project_dir, "outputs", "story-bible", "story_bible.json")
    sb = _load_json(sb_path)
    if sb:
        if "voice_guide" not in sb:
            sb["voice_guide"] = {}
        sb["voice_guide"].update(blended)
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, indent=2, ensure_ascii=False)

    return {"status": "applied", "blended_parameters": blended}


def verify_blend(project_dir: str) -> dict:
    """Verify that story_bible.voice_guide matches expected arithmetic blend."""
    result = {"valid": True, "checks": {}, "warnings": []}

    sel_path = os.path.join(project_dir, "outputs", "style-selection", "style_selection.json")
    selection = _load_json(sel_path)
    if not selection:
        result["valid"] = False
        result["checks"]["SS-BLEND"] = "FAIL"
        result["warnings"].append("style_selection.json not found")
        return result

    sb_path = os.path.join(project_dir, "outputs", "story-bible", "story_bible.json")
    sb = _load_json(sb_path)
    if not sb or "voice_guide" not in sb:
        result["valid"] = False
        result["checks"]["SS-BLEND"] = "FAIL"
        result["warnings"].append("story_bible.voice_guide not found")
        return result

    vg = sb["voice_guide"]
    metadata = vg.get("_blend_metadata", {})
    if metadata.get("computed_by") != "style_blender.py":
        result["valid"] = False
        result["checks"]["SS-BLEND"] = "FAIL"
        result["warnings"].append("voice_guide was not computed by style_blender.py")
        return result

    result["checks"]["SS-BLEND"] = "PASS"
    return result


def main():
    parser = argparse.ArgumentParser(description="Blend writing style parameters")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--apply", action="store_true", help="Compute and apply blend")
    parser.add_argument("--verify", action="store_true", help="Verify existing blend")
    args = parser.parse_args()

    if args.apply:
        result = apply_blend(args.project_dir)
    elif args.verify:
        result = verify_blend(args.project_dir)
    else:
        result = {"error": "Specify --apply or --verify"}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("valid", True) and "error" not in result else 1)


if __name__ == "__main__":
    main()
