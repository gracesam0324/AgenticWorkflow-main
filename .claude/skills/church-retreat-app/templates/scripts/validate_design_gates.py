#!/usr/bin/env python3
"""
P1 Validation: Design Quality Gates D1-D9.

Deterministic verification — H-CRITICAL level.
Checks CSS/HTML/JS patterns against design system requirements.

Usage:
    python3 validate_design_gates.py --project-dir . [--gates D1,D3] [--json]

Output (JSON to stdout):
    {"D1": {"pass": true, "value": ..., "threshold": ..., "detail": "..."}, ...}

Exit codes:
    0 = completed (check "pass" fields)
    1 = script error

SOT: Read-only — NEVER modifies files.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ── Configuration (injected during Phase 3 copy) ──
APP_TYPE = "quiz"


def read_files(project_dir, ext):
    """Read all files of given extension, skip node_modules/.git."""
    content = ""
    for root, _dirs, files in os.walk(project_dir):
        if any(skip in root for skip in ["node_modules", ".git", "scripts"]):
            continue
        for f in files:
            if f.endswith(ext):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                        content += fh.read() + "\n"
                except (UnicodeDecodeError, OSError):
                    pass
    return content


def check_d1(project_dir):
    """D1: Card UI — border-radius ≥ 12px + box-shadow exists."""
    css = read_files(project_dir, ".css")

    # Find border-radius values
    radii = re.findall(r'border-radius:\s*(\d+)', css)
    radii_vals = [int(r) for r in radii]
    all_ge_12 = all(r >= 12 for r in radii_vals) if radii_vals else False

    # Check box-shadow
    has_shadow = bool(re.search(r'box-shadow:', css))

    return {
        "pass": all_ge_12 and has_shadow,
        "value": {"min_radius": min(radii_vals) if radii_vals else 0,
                  "has_shadow": has_shadow},
        "threshold": {"min_radius": 12, "has_shadow": True},
        "detail": f"border-radius min: {min(radii_vals) if radii_vals else 0}px, "
                  f"box-shadow: {has_shadow}"
    }


def check_d2(project_dir):
    """D2: Animation — ≥ 2 transitions ≥ 150ms + page transition."""
    css = read_files(project_dir, ".css")

    # Find transition durations
    durations = re.findall(r'transition[^;]*?(\d+)ms', css)
    dur_vals = [int(d) for d in durations]
    valid_transitions = [d for d in dur_vals if d >= 150]

    # Check for page transition (keyframes or animation property)
    has_keyframes = bool(re.search(r'@keyframes\s+\w+', css))
    has_animation = bool(re.search(r'animation[^;]*:', css))
    has_page_transition = has_keyframes or has_animation

    return {
        "pass": len(valid_transitions) >= 2 and has_page_transition,
        "value": {"transition_count": len(valid_transitions),
                  "has_page_transition": has_page_transition},
        "threshold": {"transition_count": 2, "has_page_transition": True},
        "detail": f"Transitions ≥ 150ms: {len(valid_transitions)}, "
                  f"Page transition: {has_page_transition}"
    }


def check_d3(project_dir):
    """D3: Dark mode — prefers-color-scheme: dark exists."""
    css = read_files(project_dir, ".css")

    has_dark_mode = bool(re.search(r'prefers-color-scheme:\s*dark', css))

    return {
        "pass": has_dark_mode,
        "value": has_dark_mode,
        "threshold": True,
        "detail": "Dark mode media query " + ("found" if has_dark_mode else "NOT found")
    }


def check_d4(project_dir):
    """D4: Color consistency — CSS variables only, 0 hardcoded colors outside :root."""
    css = read_files(project_dir, ".css")

    # Remove :root block and var() declarations for analysis
    css_no_root = re.sub(r':root\s*\{[^}]*\}', '', css, flags=re.DOTALL)
    css_no_vars = re.sub(r'var\([^)]+\)', '', css_no_root)

    # Find hardcoded colors (hex, rgb, rgba, hsl)
    hardcoded = []
    hardcoded += re.findall(r'(?<!-)#[0-9a-fA-F]{3,8}\b', css_no_vars)
    hardcoded += re.findall(r'rgb\([^)]+\)', css_no_vars)
    hardcoded += re.findall(r'rgba\([^)]+\)', css_no_vars)
    hardcoded += re.findall(r'hsl\([^)]+\)', css_no_vars)

    # Filter out common acceptable values (black, white, transparent-like)
    acceptable = {"#000", "#fff", "#000000", "#ffffff",
                  "rgba(0, 0, 0", "rgba(255, 255, 255", "rgba(0,0,0", "rgba(255,255,255"}
    non_acceptable = [c for c in hardcoded
                      if not any(c.lower().startswith(a) for a in acceptable)]

    return {
        "pass": len(non_acceptable) == 0,
        "value": len(non_acceptable),
        "threshold": 0,
        "detail": f"{len(non_acceptable)} hardcoded color(s)" +
                  (f": {non_acceptable[:5]}" if non_acceptable else "")
    }


def check_d5(project_dir):
    """D5: Mobile native feel — fixed header + bottom tab (for applicable types)."""
    css = read_files(project_dir, ".css")
    html = read_files(project_dir, ".html")

    # Fixed header check
    has_fixed_header = bool(re.search(
        r'(?:header|\.app-header|\.navbar)[^{]*\{[^}]*position:\s*fixed',
        css, re.DOTALL
    ))
    # Also check inline or simpler patterns
    if not has_fixed_header:
        has_fixed_header = bool(re.search(r'position:\s*fixed.*top:\s*0', css, re.DOTALL))

    # Bottom tab check (required for combined and quiz)
    needs_tab = APP_TYPE in ("combined", "quiz")
    has_tab = bool(re.search(r'<nav|\.tab-bar|\.bottom-nav', html + css))

    tab_pass = has_tab if needs_tab else True

    return {
        "pass": has_fixed_header and tab_pass,
        "value": {"fixed_header": has_fixed_header, "bottom_tab": has_tab},
        "threshold": {"fixed_header": True,
                      "bottom_tab": True if needs_tab else "N/A"},
        "detail": f"Fixed header: {has_fixed_header}, "
                  f"Bottom tab: {has_tab} (required: {needs_tab})"
    }


def check_d6(project_dir):
    """D6: Font readability — body ≥ 16px, headings ≥ 24px, Pretendard loaded."""
    css = read_files(project_dir, ".css")

    # Check Pretendard
    has_pretendard = bool(re.search(r'Pretendard', css))

    # Check font-size values
    font_sizes = re.findall(r'font-size:\s*(\d+)(?:px|rem)', css)
    font_vals = [int(s) for s in font_sizes]

    # Simple heuristic: check if there's a base size >= 16 and a heading size >= 24
    has_base_16 = any(s >= 16 for s in font_vals) if font_vals else False
    has_heading_24 = any(s >= 24 for s in font_vals) if font_vals else False

    return {
        "pass": has_pretendard and has_base_16 and has_heading_24,
        "value": {"pretendard": has_pretendard, "base_16": has_base_16,
                  "heading_24": has_heading_24},
        "threshold": {"pretendard": True, "base_16": True, "heading_24": True},
        "detail": f"Pretendard: {has_pretendard}, Base ≥ 16px: {has_base_16}, "
                  f"Heading ≥ 24px: {has_heading_24}"
    }


def check_d7(project_dir):
    """D7: Micro-interactions — button scale + list stagger animation."""
    css = read_files(project_dir, ".css")
    js = read_files(project_dir, ".js")
    combined = css + js

    # Button tap scale
    has_scale = bool(re.search(r'transform:\s*scale', combined))

    # List stagger animation
    has_stagger = bool(re.search(
        r'animation-delay|stagger|nth-child.*animation|nth-child.*delay',
        combined
    ))

    return {
        "pass": has_scale and has_stagger,
        "value": {"scale": has_scale, "stagger": has_stagger},
        "threshold": {"scale": True, "stagger": True},
        "detail": f"Scale transform: {has_scale}, Stagger animation: {has_stagger}"
    }


def check_d8(project_dir):
    """D8: Loading UX — skeleton UI or spinner present."""
    html = read_files(project_dir, ".html")
    css = read_files(project_dir, ".css")
    combined = html + css

    has_skeleton = bool(re.search(r'\.skeleton|class=["\'][^"\']*skeleton', combined))
    has_loading = bool(re.search(r'\.loading|class=["\'][^"\']*loading', combined))
    has_spinner = bool(re.search(r'\.spinner|class=["\'][^"\']*spinner', combined))

    found = has_skeleton or has_loading or has_spinner

    return {
        "pass": found,
        "value": {"skeleton": has_skeleton, "loading": has_loading, "spinner": has_spinner},
        "threshold": "at least one",
        "detail": f"Skeleton: {has_skeleton}, Loading: {has_loading}, Spinner: {has_spinner}"
    }


def check_d9(project_dir):
    """D9: Screen impact — confetti + sound on /screen route."""
    js = read_files(project_dir, ".js")

    has_confetti = bool(re.search(r'confetti', js, re.IGNORECASE))
    has_sound = bool(re.search(r'AudioContext|OscillatorNode|playSound|new\s+Audio|createOscillator', js))

    return {
        "pass": has_confetti and has_sound,
        "value": {"confetti": has_confetti, "sound": has_sound},
        "threshold": {"confetti": True, "sound": True},
        "detail": f"Confetti effect: {has_confetti}, Sound effect: {has_sound}"
    }


# Gate registry
GATES = {
    "D1": check_d1, "D2": check_d2, "D3": check_d3, "D4": check_d4,
    "D5": check_d5, "D6": check_d6, "D7": check_d7, "D8": check_d8,
    "D9": check_d9,
}


def main():
    parser = argparse.ArgumentParser(description="Validate D1-D9 design quality gates")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--gates", help="Comma-separated gate list (default: all)")
    parser.add_argument("--json", action="store_true", help="JSON output to stdout")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"Project directory not found: {project_dir}"}))
        sys.exit(1)

    gate_names = args.gates.split(",") if args.gates else list(GATES.keys())
    gate_names = [g.strip().upper() for g in gate_names]

    results = {}
    for name in gate_names:
        if name in GATES:
            try:
                results[name] = GATES[name](project_dir)
            except Exception as e:
                results[name] = {"pass": False, "value": None, "threshold": None,
                                 "detail": f"Script error: {e}"}
        else:
            results[name] = {"pass": False, "value": None, "threshold": None,
                             "detail": f"Unknown gate: {name}"}

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for name, result in results.items():
            status = "PASS" if result["pass"] else "FAIL"
            print(f"{name}: {status} — {result['detail']}")


if __name__ == "__main__":
    main()
