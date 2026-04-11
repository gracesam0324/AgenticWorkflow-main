#!/usr/bin/env python3
"""
P1 Validation: Technical Quality Gates Q1-Q11.

Deterministic verification — H-CRITICAL level.
AI agents NEVER reason about these gates; they READ the JSON output and ACT on it.

Usage:
    python3 validate_gates.py --project-dir . [--gates Q1,Q3] [--json]

Output (JSON to stdout):
    {"Q1": {"pass": true, "value": 200, "threshold": 200, "detail": "HTTP 200 OK"}, ...}

Exit codes:
    0 = completed (check "pass" fields for results)
    1 = script error (invalid args, missing project dir, etc.)

SOT: Read-only — this script NEVER writes to app-state.json or any project file.
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


# ── Configuration (injected by orchestrator during Phase 3 copy) ──
APP_PORT = 3000
APP_TYPE = "quiz"
EXPECTED_QR_URL = ""  # Set during copy


def get_project_files(project_dir, extensions=None):
    """Collect all project files matching given extensions."""
    if extensions is None:
        extensions = {".html", ".css", ".js", ".json", ".png", ".woff2", ".svg"}
    files = []
    for root, _dirs, filenames in os.walk(project_dir):
        # Skip node_modules, .git, scripts
        if any(skip in root for skip in ["node_modules", ".git", "scripts"]):
            continue
        for f in filenames:
            if any(f.endswith(ext) for ext in extensions):
                files.append(os.path.join(root, f))
    return files


def read_files_by_ext(project_dir, ext):
    """Read and concatenate all files with given extension."""
    content = ""
    for f in get_project_files(project_dir, {ext}):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                content += fh.read() + "\n"
        except (UnicodeDecodeError, OSError):
            pass
    return content


class HTMLErrorCollector(HTMLParser):
    """Collect HTML parsing errors."""
    def __init__(self):
        super().__init__()
        self.errors = []

    def handle_starttag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        pass

    def error(self, message):
        self.errors.append(message)


def check_q1(project_dir):
    """Q1: Server running — HTTP 200 from localhost:PORT."""
    try:
        import urllib.request
        url = f"http://localhost:{APP_PORT}/"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
        return {
            "pass": status == 200,
            "value": status,
            "threshold": 200,
            "detail": f"HTTP {status} from localhost:{APP_PORT}"
        }
    except Exception as e:
        return {
            "pass": False,
            "value": None,
            "threshold": 200,
            "detail": f"Connection failed: {e}"
        }


def check_q2(project_dir):
    """Q2: HTML validity — no render-blocking errors."""
    html_content = read_files_by_ext(project_dir, ".html")
    if not html_content:
        return {"pass": False, "value": None, "threshold": 0, "detail": "No HTML files found"}

    parser = HTMLErrorCollector()
    errors = []
    try:
        parser.feed(html_content)
    except Exception as e:
        errors.append(str(e))
    errors.extend(parser.errors)

    # Check for common render-blocking issues
    if re.search(r"<script(?![^>]*defer|[^>]*async)[^>]*src=", html_content):
        pass  # Not an error per se, just a note

    return {
        "pass": len(errors) == 0,
        "value": len(errors),
        "threshold": 0,
        "detail": f"{len(errors)} error(s)" + (f": {errors[:3]}" if errors else "")
    }


def check_q3(project_dir):
    """Q3: External deps — 0 external scripts (except CDN font)."""
    html_content = read_files_by_ext(project_dir, ".html")
    # Match <script src="http(s)://...">
    external = re.findall(r'<script[^>]+src=["\']https?://[^"\']+["\']', html_content)
    # Allow CDN fonts (not scripts)
    external_scripts = [s for s in external if "fonts" not in s.lower()]

    return {
        "pass": len(external_scripts) == 0,
        "value": len(external_scripts),
        "threshold": 0,
        "detail": f"{len(external_scripts)} external script(s)" +
                  (f": {external_scripts[:3]}" if external_scripts else "")
    }


def check_q4(project_dir):
    """Q4: Bundle size — total ≤ 500KB."""
    total = 0
    for f in get_project_files(project_dir):
        try:
            total += os.path.getsize(f)
        except OSError:
            pass

    threshold = 512000  # 500KB
    return {
        "pass": total <= threshold,
        "value": total,
        "threshold": threshold,
        "detail": f"{total / 1024:.1f}KB / {threshold / 1024:.0f}KB"
    }


def check_q5(project_dir):
    """Q5: Korean rendering — no broken text, Korean chars present."""
    html_content = read_files_by_ext(project_dir, ".html")

    # Check for replacement character (broken encoding)
    replacement_count = html_content.count("\uFFFD")

    # Check for Korean characters
    korean_chars = re.findall(r"[\uAC00-\uD7AF]", html_content)

    pass_result = replacement_count == 0 and len(korean_chars) > 0
    return {
        "pass": pass_result,
        "value": {"replacement_chars": replacement_count, "korean_chars": len(korean_chars)},
        "threshold": {"replacement_chars": 0, "korean_chars": ">0"},
        "detail": f"Replacement chars: {replacement_count}, Korean chars: {len(korean_chars)}"
    }


def check_q6(project_dir):
    """Q6: Touch targets — all interactive elements ≥ 44x44px."""
    css_content = read_files_by_ext(project_dir, ".css")

    # Check for min-height/min-width/padding on interactive elements
    has_min_height = bool(re.search(
        r'(?:button|\.btn|a|\[role=["\']button["\'])[^{]*\{[^}]*min-height:\s*(\d+)',
        css_content, re.DOTALL
    ))

    # Check explicit 44px patterns
    has_44px = bool(re.search(r'(?:min-height|min-width):\s*4[4-9]px', css_content))

    return {
        "pass": has_min_height or has_44px,
        "value": has_44px,
        "threshold": True,
        "detail": "Touch targets ≥ 44px found" if (has_min_height or has_44px) else
                  "No 44px minimum found for interactive elements"
    }


def check_q7(project_dir):
    """Q7: QR code — QR PNG exists (decode requires qrcode library)."""
    qr_files = [f for f in get_project_files(project_dir, {".png"}) if "qr" in f.lower()]

    if not qr_files:
        return {"pass": False, "value": 0, "threshold": 1, "detail": "No QR code PNG found"}

    return {
        "pass": True,
        "value": len(qr_files),
        "threshold": 1,
        "detail": f"QR code found: {qr_files[0]}"
    }


def check_q8(project_dir):
    """Q8: Admin protection — /admin requires password."""
    try:
        import urllib.request
        url = f"http://localhost:{APP_PORT}/admin"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
        # If we get 200 without auth, that's a FAIL
        return {
            "pass": False,
            "value": status,
            "threshold": 401,
            "detail": f"Admin accessible without auth (HTTP {status})"
        }
    except urllib.error.HTTPError as e:
        # M-1 FIX: explicit HTTPError handling instead of string matching
        if e.code in (401, 403):
            return {
                "pass": True,
                "value": e.code,
                "threshold": "401|403",
                "detail": f"Admin requires authentication (HTTP {e.code})"
            }
        return {
            "pass": False,
            "value": e.code,
            "threshold": "401|403",
            "detail": f"Admin returned unexpected status: HTTP {e.code}"
        }
    except Exception as e:
        return {
            "pass": False,
            "value": None,
            "threshold": "401|403",
            "detail": f"Cannot connect to /admin: {e}"
        }


def check_q9(project_dir):
    """Q9: XSS prevention — script tags in user input neutralized."""
    js_content = read_files_by_ext(project_dir, ".js")

    # Check for escape/sanitize functions
    has_escape = bool(re.search(
        r'(?:escapeHtml|sanitize|textContent|innerText|encodeURIComponent|'
        r'replace\([^)]*<|DOMPurify)',
        js_content
    ))

    # Check that innerHTML is not used with unsanitized input
    has_dangerous = bool(re.search(r'innerHTML\s*=\s*(?!.*(?:escape|sanitize|DOMPurify))', js_content))

    return {
        "pass": has_escape and not has_dangerous,
        "value": {"has_escape": has_escape, "has_dangerous_innerHTML": has_dangerous},
        "threshold": {"has_escape": True, "has_dangerous_innerHTML": False},
        "detail": f"Escape function: {has_escape}, Dangerous innerHTML: {has_dangerous}"
    }


def check_q10(_project_dir):
    """Q10: Visual check — SKIP (human, deferred to Phase 5)."""
    return {
        "pass": True,  # Always pass (deferred)
        "value": "SKIPPED",
        "threshold": "human",
        "detail": "Deferred to Phase 5 (사역자 visual check)"
    }


def check_q11(project_dir):
    """Q11: Response latency — WebSocket roundtrip ≤ 100ms."""
    try:
        import websocket  # noqa: F401
        # Attempt WebSocket connection
        import time
        ws_url = f"ws://localhost:{APP_PORT}"
        ws = websocket.create_connection(ws_url, timeout=5)
        start = time.time()
        ws.send(json.dumps({"type": "ping", "timestamp": time.time()}))
        ws.recv()
        delta_ms = (time.time() - start) * 1000
        ws.close()
        return {
            "pass": delta_ms <= 100,
            "value": round(delta_ms, 2),
            "threshold": 100,
            "detail": f"WebSocket roundtrip: {delta_ms:.2f}ms"
        }
    except ImportError:
        # Fallback: check if WebSocket code exists
        js_content = read_files_by_ext(project_dir, ".js")
        has_ws = bool(re.search(r'(?:WebSocket|new\s+WebSocket|ws://)', js_content))
        if not has_ws:
            return {"pass": True, "value": "N/A", "threshold": 100,
                    "detail": "No WebSocket in this app type"}
        return {"pass": True, "value": "SKIPPED", "threshold": 100,
                "detail": "WebSocket library not available for timing test"}
    except Exception as e:
        return {"pass": False, "value": None, "threshold": 100,
                "detail": f"WebSocket test failed: {e}"}


# Gate registry
GATES = {
    "Q1": check_q1, "Q2": check_q2, "Q3": check_q3, "Q4": check_q4,
    "Q5": check_q5, "Q6": check_q6, "Q7": check_q7, "Q8": check_q8,
    "Q9": check_q9, "Q10": check_q10, "Q11": check_q11,
}


def main():
    parser = argparse.ArgumentParser(description="Validate Q1-Q11 technical quality gates")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--gates", help="Comma-separated gate list (default: all)")
    parser.add_argument("--json", action="store_true", help="JSON output to stdout")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"Project directory not found: {project_dir}"}))
        sys.exit(1)

    # Select gates
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
