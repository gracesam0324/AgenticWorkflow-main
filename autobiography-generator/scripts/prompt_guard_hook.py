#!/usr/bin/env python3
"""
Pre-Commit Hook for Prompt Changes.

Detects changes to .claude/agents/*.md files, runs golden tests for changed
agents, blocks commit if quality regresses, and shows a comparison report.

This hook is designed to be called from:
1. A git pre-commit hook (via .git/hooks/pre-commit)
2. Claude Code's PreToolUse hook (via .claude/settings.json)
3. Directly from CI/CD pipelines

Usage as git hook:
    # Install: symlink or copy to .git/hooks/pre-commit
    ln -sf ../../autobiography-generator/scripts/prompt_guard_hook.py .git/hooks/pre-commit

Usage standalone:
    python3 prompt_guard_hook.py                    # Check staged changes
    python3 prompt_guard_hook.py --check-file .claude/agents/reviewer.md
    python3 prompt_guard_hook.py --dry-run           # Show what would run, don't block
    python3 prompt_guard_hook.py --force-run          # Run tests even if no prompts changed

Exit codes:
    0 = OK (commit allowed)
    1 = Quality regression detected (commit blocked)
    2 = Error in hook execution
"""

import json
import os
import re
import subprocess
import sys
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # autobiography-generator/../
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
PROMPT_HASH_STORE = SCRIPT_DIR / ".prompt-hashes.json"
GOLDEN_TEST_SCRIPT = SCRIPT_DIR / "test_quality.py"
VOICE_CHECK_SCRIPT = SCRIPT_DIR / "check_voice.py"

# Files we monitor for prompt changes
MONITORED_PATTERNS = [
    ".claude/agents/*.md",
    ".claude/skills/*/SKILL.md",
    ".claude/skills/*/references/*.md",
    "autobiography-generator/templates/*.md",
]

# Mapping: which golden tests are affected by which agent files
AGENT_TEST_MAP = {
    "reviewer.md": ["GT-001", "GT-002", "GT-003", "GT-004", "GT-005"],
    "translator.md": [],  # Translation tests handled separately
    "fact-checker.md": ["GT-002", "GT-003", "GT-005"],
}


# ---------------------------------------------------------------------------
# Git Integration
# ---------------------------------------------------------------------------

def get_staged_files() -> list[str]:
    """Get list of files staged for commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except Exception:
        return []


def get_staged_diff(filepath: str) -> str:
    """Get the staged diff for a specific file."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--", filepath],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        return result.stdout
    except Exception:
        return ""


def get_file_hash(filepath: str) -> str:
    """Compute hash of a file's current content."""
    full_path = PROJECT_ROOT / filepath
    if full_path.exists():
        content = full_path.read_text()
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    return ""


# ---------------------------------------------------------------------------
# Prompt Change Detection
# ---------------------------------------------------------------------------

def detect_prompt_changes(staged_files: list[str]) -> list[dict]:
    """
    Identify which staged files are prompt/agent definition changes.
    Returns list of change records.
    """
    import fnmatch

    changes = []
    for filepath in staged_files:
        for pattern in MONITORED_PATTERNS:
            if fnmatch.fnmatch(filepath, pattern):
                diff = get_staged_diff(filepath)
                changes.append({
                    "file": filepath,
                    "pattern_matched": pattern,
                    "hash": get_file_hash(filepath),
                    "diff_lines": len(diff.split("\n")),
                    "diff_preview": diff[:500] if diff else "(no diff)",
                })
                break
    return changes


def load_prompt_hashes() -> dict:
    """Load stored prompt file hashes from last successful commit."""
    if PROMPT_HASH_STORE.exists():
        return json.loads(PROMPT_HASH_STORE.read_text())
    return {}


def save_prompt_hashes(hashes: dict) -> None:
    """Save current prompt file hashes after successful commit."""
    PROMPT_HASH_STORE.write_text(json.dumps(hashes, indent=2))


def identify_changed_since_baseline(changes: list[dict]) -> list[dict]:
    """
    Compare current file hashes against stored baseline.
    Identifies only genuinely changed files (not just re-staged).
    """
    stored = load_prompt_hashes()
    genuinely_changed = []

    for change in changes:
        stored_hash = stored.get(change["file"])
        if stored_hash != change["hash"]:
            change["previous_hash"] = stored_hash
            change["is_new"] = stored_hash is None
            genuinely_changed.append(change)

    return genuinely_changed


# ---------------------------------------------------------------------------
# Quality Gate: Run Golden Tests
# ---------------------------------------------------------------------------

def run_golden_tests(test_ids: Optional[list[str]] = None) -> dict:
    """
    Run the golden test suite, optionally filtered to specific test IDs.
    Returns test results summary.
    """
    if not GOLDEN_TEST_SCRIPT.exists():
        return {"error": f"Test script not found: {GOLDEN_TEST_SCRIPT}"}

    cmd = [sys.executable, str(GOLDEN_TEST_SCRIPT), "--compare-baseline", "--report-format", "json"]

    if test_ids:
        # Run each specified test separately and aggregate
        all_results = {}
        for tid in test_ids:
            result = subprocess.run(
                [sys.executable, str(GOLDEN_TEST_SCRIPT), "--test-id", tid,
                 "--compare-baseline", "--report-format", "json"],
                capture_output=True, text=True, cwd=str(SCRIPT_DIR),
                timeout=300,
            )
            try:
                parsed = json.loads(result.stdout)
                all_results.update(parsed.get("results", {}))
            except (json.JSONDecodeError, AttributeError):
                all_results[tid] = {"error": result.stderr or "Parse error"}
        return {"results": all_results, "exit_code": 0}
    else:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(SCRIPT_DIR),
            timeout=600,
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "error": "Could not parse test output",
                "stdout": result.stdout[:1000],
                "stderr": result.stderr[:1000],
                "exit_code": result.returncode,
            }


def determine_affected_tests(changes: list[dict]) -> list[str]:
    """
    Given a list of changed files, determine which golden tests to run.
    Conservative: if mapping unknown, run all tests.
    """
    test_ids = set()
    run_all = False

    for change in changes:
        filename = Path(change["file"]).name
        if filename in AGENT_TEST_MAP:
            mapped = AGENT_TEST_MAP[filename]
            if mapped:
                test_ids.update(mapped)
            # Empty list means this file doesn't affect generation tests
        else:
            # Unknown file changed — run all tests to be safe
            run_all = True
            break

    if run_all:
        return []  # Empty list signals "run all"
    return sorted(test_ids)


# ---------------------------------------------------------------------------
# Diff Analysis
# ---------------------------------------------------------------------------

def analyze_prompt_diff(diff_text: str) -> dict:
    """
    Analyze what kind of changes were made to a prompt file.
    Categorizes changes as structural, behavioral, or cosmetic.
    """
    added_lines = [l[1:] for l in diff_text.split("\n") if l.startswith("+") and not l.startswith("+++")]
    removed_lines = [l[1:] for l in diff_text.split("\n") if l.startswith("-") and not l.startswith("---")]

    # Behavioral keywords that might affect output quality
    behavioral_keywords = [
        "must", "never", "always", "important", "critical", "required",
        "tone", "voice", "style", "format", "structure", "length",
        "persona", "role", "instruction", "constraint", "rule",
        "temperature", "model", "max_tokens",
    ]

    behavioral_changes = 0
    for line in added_lines + removed_lines:
        lower = line.lower()
        if any(kw in lower for kw in behavioral_keywords):
            behavioral_changes += 1

    # Structural changes (headers, sections)
    structural_changes = sum(1 for l in added_lines + removed_lines if l.strip().startswith("#"))

    # Cosmetic changes (whitespace, typo fixes)
    cosmetic = len(added_lines) + len(removed_lines) - behavioral_changes - structural_changes

    total = len(added_lines) + len(removed_lines)
    risk_level = "low"
    if behavioral_changes > 5 or structural_changes > 3:
        risk_level = "high"
    elif behavioral_changes > 2 or structural_changes > 1:
        risk_level = "medium"

    return {
        "total_changed_lines": total,
        "added_lines": len(added_lines),
        "removed_lines": len(removed_lines),
        "behavioral_changes": behavioral_changes,
        "structural_changes": structural_changes,
        "cosmetic_changes": max(cosmetic, 0),
        "risk_level": risk_level,
    }


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def format_hook_report(
    changes: list[dict],
    test_results: Optional[dict],
    should_block: bool,
    dry_run: bool,
) -> str:
    """Format the pre-commit hook report."""
    lines = []
    lines.append("")
    lines.append("=" * 64)
    lines.append("  PROMPT CHANGE QUALITY GATE")
    lines.append("=" * 64)

    if dry_run:
        lines.append("  MODE: DRY RUN (commit will NOT be blocked)")
    lines.append("")

    # Changed files
    lines.append(f"  Prompt changes detected: {len(changes)}")
    for change in changes:
        status = "NEW" if change.get("is_new") else "MODIFIED"
        lines.append(f"    [{status}] {change['file']}")
        diff = get_staged_diff(change["file"])
        if diff:
            analysis = analyze_prompt_diff(diff)
            lines.append(
                f"           Risk: {analysis['risk_level'].upper()} "
                f"(+{analysis['added_lines']}/-{analysis['removed_lines']} lines, "
                f"{analysis['behavioral_changes']} behavioral changes)"
            )
    lines.append("")

    # Test results
    if test_results:
        if "error" in test_results:
            lines.append(f"  Test execution error: {test_results['error']}")
        else:
            results = test_results.get("results", {})
            regression = test_results.get("regression", {})

            passed = sum(1 for r in results.values() if r.get("overall_passed"))
            total = len(results)
            lines.append(f"  Golden tests: {passed}/{total} passed")

            for tid, result in sorted(results.items()):
                status = "PASS" if result.get("overall_passed") else "FAIL"
                score = result.get("weighted_score", 0)
                lines.append(f"    [{status}] {tid}: {score:.3f}")

            if regression:
                reg_list = regression.get("regressions", [])
                if reg_list:
                    lines.append(f"\n  Regressions detected: {len(reg_list)}")
                    for r in reg_list:
                        lines.append(
                            f"    [{r['severity']}] {r['test_id']}/{r['dimension']}: "
                            f"{r['baseline']:.3f} -> {r['current']:.3f} ({r['delta']:+.3f})"
                        )
                imp_list = regression.get("improvements", [])
                if imp_list:
                    lines.append(f"\n  Improvements: {len(imp_list)}")
                    for imp in imp_list:
                        lines.append(
                            f"    [UP] {imp['test_id']}/{imp['dimension']}: "
                            f"{imp['baseline']:.3f} -> {imp['current']:.3f} ({imp['delta']:+.3f})"
                        )
    else:
        lines.append("  No golden tests executed (no API key or dry-run mode)")

    lines.append("")
    if should_block and not dry_run:
        lines.append("  RESULT: COMMIT BLOCKED — quality regression detected")
        lines.append("  Fix the issues above or run with --no-verify to override")
    elif should_block and dry_run:
        lines.append("  RESULT: WOULD BLOCK (dry-run mode, commit allowed)")
    else:
        lines.append("  RESULT: COMMIT ALLOWED")
        # Update stored hashes on success
        hashes = load_prompt_hashes()
        for change in changes:
            hashes[change["file"]] = change["hash"]
        save_prompt_hashes(hashes)
        lines.append("  Prompt hashes updated for future regression detection")

    lines.append("=" * 64)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude Code Hook Integration
# ---------------------------------------------------------------------------

def run_as_claude_hook() -> int:
    """
    Entry point when called as a Claude Code PreToolUse hook.
    Reads tool input from stdin (JSON), checks if it's a git commit,
    and runs quality checks if prompt files are staged.
    """
    # Read hook input
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return 0  # Not a hook call, pass through

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept git commit commands
    if tool_name != "Bash":
        return 0

    command = tool_input.get("command", "")
    if "git commit" not in command:
        return 0

    # Check for staged prompt changes
    staged = get_staged_files()
    changes = detect_prompt_changes(staged)
    if not changes:
        return 0  # No prompt changes, allow commit

    genuinely_changed = identify_changed_since_baseline(changes)
    if not genuinely_changed:
        return 0  # Files haven't actually changed since last baseline

    # Determine affected tests
    test_ids = determine_affected_tests(genuinely_changed)

    # Run quality checks (with baseline comparison)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    test_results = None
    should_block = False

    if api_key:
        test_results = run_golden_tests(test_ids if test_ids else None)
        regression = test_results.get("regression", {})
        should_block = regression.get("should_block", False)

        # Also block if any test outright failed
        results = test_results.get("results", {})
        if any(not r.get("overall_passed") for r in results.values()):
            should_block = True

    report = format_hook_report(genuinely_changed, test_results, should_block, dry_run=False)

    if should_block:
        # Output as block message (exit 2 for Claude Code hooks)
        print(json.dumps({"result": "block", "reason": report}))
        return 2
    else:
        print(json.dumps({"result": "pass", "message": report}))
        return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pre-Commit Hook for Prompt Changes")
    parser.add_argument("--check-file", type=str, help="Check a specific file")
    parser.add_argument("--dry-run", action="store_true", help="Don't block, just report")
    parser.add_argument("--force-run", action="store_true", help="Run tests even without changes")
    parser.add_argument("--claude-hook", action="store_true", help="Run as Claude Code hook (reads stdin)")
    parser.add_argument("--install", action="store_true", help="Install as git pre-commit hook")
    args = parser.parse_args()

    # Installation mode
    if args.install:
        git_hook_path = PROJECT_ROOT / ".git" / "hooks" / "pre-commit"
        hook_content = f"""#!/bin/sh
# Auto-generated by prompt_guard_hook.py
python3 "{Path(__file__).resolve()}" "$@"
exit $?
"""
        git_hook_path.write_text(hook_content)
        git_hook_path.chmod(0o755)
        print(f"Installed pre-commit hook: {git_hook_path}")
        sys.exit(0)

    # Claude Code hook mode
    if args.claude_hook:
        sys.exit(run_as_claude_hook())

    # Standalone mode
    if args.check_file:
        staged = [args.check_file]
    elif args.force_run:
        staged = []
        # Load all monitored files
        import glob as globmod
        for pattern in MONITORED_PATTERNS:
            staged.extend(globmod.glob(str(PROJECT_ROOT / pattern)))
        staged = [os.path.relpath(f, PROJECT_ROOT) for f in staged]
    else:
        staged = get_staged_files()

    changes = detect_prompt_changes(staged) if not args.force_run else [
        {"file": f, "hash": get_file_hash(f), "diff_lines": 0, "is_new": False}
        for f in staged
    ]

    if not changes and not args.force_run:
        print("No prompt changes detected. Commit allowed.")
        sys.exit(0)

    genuinely_changed = identify_changed_since_baseline(changes) if not args.force_run else changes

    if not genuinely_changed and not args.force_run:
        print("Prompt files staged but unchanged since last baseline. Commit allowed.")
        sys.exit(0)

    print(f"Detected {len(genuinely_changed)} prompt change(s). Running quality checks...")

    # Determine which tests to run
    test_ids = determine_affected_tests(genuinely_changed)
    print(f"Affected tests: {test_ids if test_ids else 'ALL'}")

    # Run golden tests
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    test_results = None
    should_block = False

    if api_key:
        print("Running golden test suite...")
        test_results = run_golden_tests(test_ids if test_ids else None)
        regression = test_results.get("regression", {})
        should_block = regression.get("should_block", False)

        results = test_results.get("results", {})
        if any(not r.get("overall_passed") for r in results.values()):
            should_block = True
    else:
        print("[WARN] ANTHROPIC_API_KEY not set. Skipping LLM-based quality checks.")
        print("[WARN] Only structural analysis will be performed.")

    report = format_hook_report(genuinely_changed, test_results, should_block, args.dry_run)
    print(report)

    if should_block and not args.dry_run:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
