#!/usr/bin/env python3
"""
P1 Validation: Integration Verification (T-3.11).

Cross-references HTML classes ↔ CSS selectors, JS DOM refs ↔ HTML IDs,
manifest start_url, service worker cache list.

H-CRITICAL — deterministic, no AI reasoning.

Usage:
    python3 validate_integration.py --project-dir . [--json]

Output (JSON): {"html_css": {...}, "js_html": {...}, "manifest": {...}, "sw_cache": {...}}
SOT: Read-only.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def read_files(project_dir, ext):
    """Read all files of given extension."""
    content = ""
    paths = []
    for root, _dirs, files in os.walk(project_dir):
        if any(skip in root for skip in ["node_modules", ".git", "scripts"]):
            continue
        for f in files:
            if f.endswith(ext):
                path = os.path.join(root, f)
                paths.append(path)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content += fh.read() + "\n"
                except (UnicodeDecodeError, OSError):
                    pass
    return content, paths


def check_html_css(project_dir):
    """Check HTML classes are defined in CSS."""
    html, _ = read_files(project_dir, ".html")
    css, _ = read_files(project_dir, ".css")

    # Extract HTML classes
    html_classes = set()
    for match in re.finditer(r'class=["\']([^"\']+)["\']', html):
        for cls in match.group(1).split():
            html_classes.add(cls)

    # Extract CSS class selectors
    css_classes = set()
    for match in re.finditer(r'\.([a-zA-Z][\w-]*)', css):
        css_classes.add(match.group(1))

    # Orphaned = used in HTML but not defined in CSS
    orphaned = html_classes - css_classes

    # Filter common utility/framework classes
    common = {"active", "hidden", "show", "fade", "in", "out", "open", "closed",
              "disabled", "selected", "checked", "error", "success", "loading"}
    orphaned = orphaned - common

    return {
        "pass": len(orphaned) == 0,
        "value": {"html_classes": len(html_classes), "css_classes": len(css_classes),
                  "orphaned": sorted(list(orphaned))[:10]},
        "threshold": 0,
        "detail": f"{len(orphaned)} orphaned class(es)" +
                  (f": {sorted(list(orphaned))[:5]}" if orphaned else "")
    }


def check_js_html(project_dir):
    """Check JS DOM references point to existing HTML IDs."""
    html, _ = read_files(project_dir, ".html")
    js, _ = read_files(project_dir, ".js")

    # Extract JS DOM references
    js_refs = set()
    for match in re.finditer(r'getElementById\(["\'](\w+)["\']', js):
        js_refs.add(match.group(1))
    for match in re.finditer(r'querySelector\(["\']#([^"\']+)["\']', js):
        js_refs.add(match.group(1))

    # Extract HTML IDs
    html_ids = set()
    for match in re.finditer(r'id=["\']([^"\']+)["\']', html):
        html_ids.add(match.group(1))

    # Dangling refs = JS references to IDs that don't exist in HTML
    dangling = js_refs - html_ids

    return {
        "pass": len(dangling) == 0,
        "value": {"js_refs": len(js_refs), "html_ids": len(html_ids),
                  "dangling": sorted(list(dangling))[:10]},
        "threshold": 0,
        "detail": f"{len(dangling)} dangling ref(s)" +
                  (f": {sorted(list(dangling))[:5]}" if dangling else "")
    }


def check_manifest(project_dir):
    """Check manifest.json start_url points to existing file/route."""
    manifest_path = None
    for root, _dirs, files in os.walk(project_dir):
        if any(skip in root for skip in ["node_modules", ".git"]):
            continue
        if "manifest.json" in files:
            manifest_path = os.path.join(root, "manifest.json")
            break

    if not manifest_path:
        return {"pass": True, "value": "N/A", "threshold": "exists",
                "detail": "No manifest.json found (OK for non-PWA)"}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"pass": False, "value": None, "threshold": "valid JSON",
                "detail": f"manifest.json parse error: {e}"}

    start_url = manifest.get("start_url", "/")

    # Check if start_url file exists (for static apps)
    if start_url in ("/", "./", "./index.html"):
        index_exists = os.path.exists(os.path.join(project_dir, "index.html"))
        return {
            "pass": index_exists,
            "value": start_url,
            "threshold": "file exists",
            "detail": f"start_url '{start_url}' → index.html {'exists' if index_exists else 'MISSING'}"
        }

    return {"pass": True, "value": start_url, "threshold": "valid",
            "detail": f"start_url: {start_url} (server-routed)"}


def check_sw_cache(project_dir):
    """Check service worker cache list — all listed files exist."""
    sw_path = None
    for root, _dirs, files in os.walk(project_dir):
        if any(skip in root for skip in ["node_modules", ".git"]):
            continue
        for f in files:
            if "service-worker" in f or f == "sw.js":
                sw_path = os.path.join(root, f)
                break

    if not sw_path:
        return {"pass": True, "value": "N/A", "threshold": "exists",
                "detail": "No service worker found (OK for non-PWA)"}

    try:
        with open(sw_path, "r", encoding="utf-8") as f:
            sw_content = f.read()
    except OSError as e:
        return {"pass": False, "value": None, "threshold": "readable",
                "detail": f"Cannot read service worker: {e}"}

    # Extract cached file paths from service worker
    cached_files = re.findall(r'["\']([./][\w/.-]+)["\']', sw_content)
    cached_files = [f for f in cached_files if not f.startswith("//")]

    missing = []
    for cached in cached_files:
        clean_path = cached.lstrip("./")
        if clean_path and not os.path.exists(os.path.join(project_dir, clean_path)):
            missing.append(cached)

    return {
        "pass": len(missing) == 0,
        "value": {"total_cached": len(cached_files), "missing": missing[:10]},
        "threshold": 0,
        "detail": f"{len(missing)} cached file(s) missing" +
                  (f": {missing[:5]}" if missing else "")
    }


def main():
    parser = argparse.ArgumentParser(description="Validate integration (T-3.11)")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"Directory not found: {project_dir}"}))
        sys.exit(1)

    results = {
        "html_css": check_html_css(project_dir),
        "js_html": check_js_html(project_dir),
        "manifest": check_manifest(project_dir),
        "sw_cache": check_sw_cache(project_dir),
    }

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for name, result in results.items():
            status = "PASS" if result["pass"] else "FAIL"
            print(f"{name}: {status} — {result['detail']}")


if __name__ == "__main__":
    main()
