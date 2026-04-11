#!/usr/bin/env python3
"""TDD Guard — blocks source modifications when tests fail.
Section 21.2: Skips if .tdd-guard absent or target file doesn't exist yet."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _resolve_project_dir() -> Path:
    """Resolve the autobiography-generator project root."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()


def _get_target_file(project_dir: Path) -> str | None:
    """Extract the target file path from CLAUDE_TOOL_INPUT.

    Works for both Write (file_path) and Edit (file_path) tool inputs.
    Returns absolute path or None.
    """
    tool_input_raw = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    try:
        tool_input = json.loads(tool_input_raw)
    except json.JSONDecodeError:
        return None

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None

    # Resolve to absolute
    if not os.path.isabs(file_path):
        file_path = str(project_dir / file_path)

    return file_path


def _load_tdd_guard(tdd_guard_path: Path) -> dict:
    """Load and parse the .tdd-guard YAML file.

    Expected format:
        # .tdd-guard — source-to-test mapping
        scripts/sot_lib.py: tests/test_state_file.py
        scripts/quality_gate_check.py: tests/test_quality_gate.py
        scripts/schema_validator.py: tests/test_story_bible_schema.py

    Returns a dict mapping source paths to test paths (both relative).
    """
    mapping: dict[str, str] = {}

    try:
        import yaml
        with open(tdd_guard_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
        return {}
    except ImportError:
        pass
    except Exception:
        return {}

    # Fallback: simple line-by-line parsing (handles key: value YAML subset)
    try:
        with open(tdd_guard_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    src, test = line.split(":", 1)
                    src = src.strip().strip('"').strip("'")
                    test = test.strip().strip('"').strip("'")
                    if src and test:
                        mapping[src] = test
    except OSError:
        pass

    return mapping


def _find_related_tests(
    target_file: str,
    project_dir: Path,
    mapping: dict[str, str],
) -> list[str]:
    """Find test files related to the target source file.

    Uses the .tdd-guard mapping to find the test file(s).
    Returns a list of absolute paths to test files.
    """
    try:
        rel_target = os.path.relpath(target_file, project_dir)
    except ValueError:
        rel_target = target_file

    # Normalize path separators
    rel_target = rel_target.replace("\\", "/")

    tests = []

    for src_pattern, test_path in mapping.items():
        src_pattern = src_pattern.replace("\\", "/")
        test_path = test_path.replace("\\", "/")

        # Exact match or suffix match (e.g., "sot_lib.py" matches "scripts/sot_lib.py")
        if rel_target == src_pattern or rel_target.endswith("/" + src_pattern):
            abs_test = project_dir / test_path
            if abs_test.is_file():
                tests.append(str(abs_test))

    return tests


def _run_tests(test_files: list[str], project_dir: Path) -> tuple[bool, str]:
    """Run the specified test files via pytest.

    Returns (passed: bool, output: str).
    """
    # Prefer the project venv Python, fall back to system
    venv_python = project_dir / ".venv" / "bin" / "python3"
    python_cmd = str(venv_python) if venv_python.is_file() else "python3"

    cmd = [
        python_cmd, "-m", "pytest",
        *test_files,
        "-q", "--no-header", "--tb=short", "-x",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(project_dir),
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output += "\n" + result.stderr.strip()

        return result.returncode == 0, output

    except subprocess.TimeoutExpired:
        return False, "TDD Guard: Test execution timed out (60s limit)."
    except FileNotFoundError:
        return True, "TDD Guard: pytest not found — skipping (allow)."
    except OSError as e:
        return True, f"TDD Guard: Test execution error — {e}. Skipping (allow)."


def main() -> None:
    """Entry point — enforce TDD discipline on source file modifications."""
    project_dir = _resolve_project_dir()

    # ── Gate 1: .tdd-guard must exist (Build Phase only) ─────────────
    tdd_guard_path = project_dir / ".tdd-guard"
    if not tdd_guard_path.is_file():
        # Section 21.2: SKIP if .tdd-guard absent — Build Phase not active
        sys.exit(0)

    # ── Gate 2: Determine target file ────────────────────────────────
    target_file = _get_target_file(project_dir)
    if target_file is None:
        sys.exit(0)

    # ── Gate 3: SKIP if target file doesn't exist yet (initial creation) ──
    if not os.path.isfile(target_file):
        # Creating a new file, not modifying existing — allow
        sys.exit(0)

    # ── Gate 4: Load the source-to-test mapping ──────────────────────
    mapping = _load_tdd_guard(tdd_guard_path)
    if not mapping:
        # Empty or unreadable .tdd-guard — allow
        sys.exit(0)

    # ── Gate 5: Find related tests ───────────────────────────────────
    related_tests = _find_related_tests(target_file, project_dir, mapping)
    if not related_tests:
        # No tests mapped for this source file — allow
        sys.exit(0)

    # ── Run the related tests ────────────────────────────────────────
    passed, output = _run_tests(related_tests, project_dir)

    if passed:
        test_names = [os.path.basename(t) for t in related_tests]
        print(
            f"TDD GUARD PASS — Tests passed for "
            f"{os.path.basename(target_file)}: {', '.join(test_names)}",
            file=sys.stderr,
        )
        sys.exit(0)

    # ── Tests failed — block the edit ────────────────────────────────
    try:
        rel_target = os.path.relpath(target_file, project_dir)
    except ValueError:
        rel_target = target_file

    lines = [
        f"TDD GUARD REJECT — Cannot modify '{rel_target}' while its tests fail.",
        "",
        "Failed test output:",
        output[-1000:] if len(output) > 1000 else output,  # Cap output
        "",
        "Fix the failing tests first, then retry the edit.",
    ]
    print("\n".join(lines), file=sys.stderr)
    sys.exit(2)  # Block the write/edit


if __name__ == "__main__":
    main()
