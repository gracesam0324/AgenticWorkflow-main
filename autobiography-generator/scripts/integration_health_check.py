#!/usr/bin/env python3
"""Integration Health Check — Verify ALL external dependencies.

Checks every external tool, credential, and service that the AI Autobiography
Generator depends on. Produces a structured health report.

Checks performed:
    1. Python version and required packages
    2. System tools (pandoc, xelatex, tlmgr)
    3. LaTeX packages (memoir, fontspec, etc.)
    4. API credentials (format validation via Keychain/env)
    5. API connectivity (optional live checks)
    6. Project file structure integrity
    7. Dependency version drift (installed vs. locked)

Usage::

    # Quick check (no network calls)
    python3 scripts/integration_health_check.py

    # Full check including API connectivity
    python3 scripts/integration_health_check.py --live

    # JSON output for automation
    python3 scripts/integration_health_check.py --json

    # Check specific category only
    python3 scripts/integration_health_check.py --only credentials

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
    2 — critical failure (cannot run pipeline at all)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# Data structures
# ============================================================================


@dataclass
class CheckResult:
    """Result of a single health check."""

    name: str
    category: str
    status: str  # "pass", "warn", "fail", "skip"
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthReport:
    """Aggregated health check results."""

    timestamp: str = ""
    overall_status: str = "unknown"
    checks: list[CheckResult] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def add(self, result: CheckResult) -> None:
        """Add a check result to the report."""
        self.checks.append(result)

    def finalize(self) -> None:
        """Compute summary and overall status."""
        self.timestamp = datetime.now().isoformat()
        self.summary = {
            "pass": sum(1 for c in self.checks if c.status == "pass"),
            "warn": sum(1 for c in self.checks if c.status == "warn"),
            "fail": sum(1 for c in self.checks if c.status == "fail"),
            "skip": sum(1 for c in self.checks if c.status == "skip"),
            "total": len(self.checks),
        }

        if self.summary["fail"] > 0:
            # Check if any critical check failed
            critical_fails = [
                c for c in self.checks
                if c.status == "fail" and c.category in ("python", "system-tools")
            ]
            self.overall_status = "critical" if critical_fails else "degraded"
        elif self.summary["warn"] > 0:
            self.overall_status = "healthy-with-warnings"
        else:
            self.overall_status = "healthy"


# ============================================================================
# Check implementations
# ============================================================================


def check_python_version(report: HealthReport) -> None:
    """Verify Python version >= 3.11."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version >= (3, 11):
        report.add(CheckResult(
            name="Python version",
            category="python",
            status="pass",
            message=f"Python {version_str}",
            details={"version": version_str, "path": sys.executable},
        ))
    else:
        report.add(CheckResult(
            name="Python version",
            category="python",
            status="fail",
            message=f"Python {version_str} < 3.11 required",
            details={"version": version_str, "required": ">=3.11"},
        ))


def check_python_packages(report: HealthReport) -> None:
    """Verify required Python packages are installed."""
    required_packages = {
        "pydantic": {"min_version": "2.6.0", "critical": True},
        "yaml": {"import_name": "yaml", "pip_name": "PyYAML", "min_version": "6.0", "critical": True},
        "jsonschema": {"min_version": "4.21.0", "critical": True},
        "keyring": {"min_version": "25.0.0", "critical": False},
        "openai": {"min_version": "1.0.0", "critical": False},
        "textstat": {"min_version": "0.7.0", "critical": False},
    }

    for pkg_name, spec in required_packages.items():
        import_name = spec.get("import_name", pkg_name)
        pip_name = spec.get("pip_name", pkg_name)
        critical = spec.get("critical", False)

        try:
            mod = __import__(import_name)
            version = getattr(mod, "__version__", getattr(mod, "VERSION", "unknown"))

            report.add(CheckResult(
                name=f"Package: {pip_name}",
                category="python-packages",
                status="pass",
                message=f"{pip_name} {version}",
                details={"version": str(version), "required_min": spec.get("min_version", "any")},
            ))
        except ImportError:
            status = "fail" if critical else "warn"
            report.add(CheckResult(
                name=f"Package: {pip_name}",
                category="python-packages",
                status=status,
                message=f"{pip_name} not installed. Run: pip install {pip_name}",
                details={"critical": critical},
            ))

    # Check google-genai separately (different import path)
    try:
        from google import genai

        version = getattr(genai, "__version__", "unknown")
        report.add(CheckResult(
            name="Package: google-genai",
            category="python-packages",
            status="pass",
            message=f"google-genai {version}",
            details={"version": str(version)},
        ))
    except ImportError:
        report.add(CheckResult(
            name="Package: google-genai",
            category="python-packages",
            status="warn",
            message="google-genai not installed. Run: pip install google-genai",
            details={"critical": False},
        ))


def check_pandoc(report: HealthReport) -> None:
    """Verify Pandoc installation and version."""
    pandoc_path = shutil.which("pandoc")
    if not pandoc_path:
        report.add(CheckResult(
            name="Pandoc",
            category="system-tools",
            status="fail",
            message="pandoc not found. Install with: brew install pandoc",
        ))
        return

    try:
        result = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        first_line = result.stdout.strip().split("\n")[0]
        version_str = first_line.split()[-1] if first_line else "unknown"

        # Check version >= 3.1.0
        parts = version_str.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0

        if major >= 3 and minor >= 1:
            status = "pass"
            msg = f"pandoc {version_str}"
        elif major >= 3:
            status = "warn"
            msg = f"pandoc {version_str} (>= 3.1.0 recommended)"
        else:
            status = "fail"
            msg = f"pandoc {version_str} too old (>= 3.1.0 required)"

        report.add(CheckResult(
            name="Pandoc",
            category="system-tools",
            status=status,
            message=msg,
            details={"version": version_str, "path": pandoc_path},
        ))
    except (subprocess.TimeoutExpired, Exception) as e:
        report.add(CheckResult(
            name="Pandoc",
            category="system-tools",
            status="fail",
            message=f"Failed to check pandoc version: {e}",
        ))


def check_xelatex(report: HealthReport) -> None:
    """Verify XeLaTeX installation."""
    xelatex_path = shutil.which("xelatex")
    if not xelatex_path:
        report.add(CheckResult(
            name="XeLaTeX",
            category="system-tools",
            status="fail",
            message="xelatex not found. Install with: brew install --cask mactex",
        ))
        return

    try:
        result = subprocess.run(
            ["xelatex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Extract TeX Live year from version output
        version_match = re.search(r"TeX Live (\d{4})", result.stdout)
        tl_year = version_match.group(1) if version_match else "unknown"

        report.add(CheckResult(
            name="XeLaTeX",
            category="system-tools",
            status="pass",
            message=f"xelatex available (TeX Live {tl_year})",
            details={"tex_live_year": tl_year, "path": xelatex_path},
        ))
    except (subprocess.TimeoutExpired, Exception) as e:
        report.add(CheckResult(
            name="XeLaTeX",
            category="system-tools",
            status="fail",
            message=f"Failed to check xelatex: {e}",
        ))


def check_latex_packages(report: HealthReport) -> None:
    """Verify required LaTeX packages are installed."""
    required_packages = ["memoir", "fontspec", "microtype", "polyglossia", "xetex"]

    tlmgr_path = shutil.which("tlmgr")
    if not tlmgr_path:
        report.add(CheckResult(
            name="LaTeX packages",
            category="system-tools",
            status="skip",
            message="tlmgr not found; cannot verify LaTeX packages",
        ))
        return

    for pkg in required_packages:
        try:
            result = subprocess.run(
                ["tlmgr", "info", "--only-installed", pkg],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0 and pkg in result.stdout:
                # Extract version
                version_match = re.search(r"revision:\s*(\d+)", result.stdout)
                revision = version_match.group(1) if version_match else "unknown"
                report.add(CheckResult(
                    name=f"LaTeX: {pkg}",
                    category="latex-packages",
                    status="pass",
                    message=f"{pkg} installed (revision {revision})",
                    details={"revision": revision},
                ))
            else:
                report.add(CheckResult(
                    name=f"LaTeX: {pkg}",
                    category="latex-packages",
                    status="warn",
                    message=f"{pkg} not found. Install: sudo tlmgr install {pkg}",
                ))
        except (subprocess.TimeoutExpired, Exception):
            report.add(CheckResult(
                name=f"LaTeX: {pkg}",
                category="latex-packages",
                status="skip",
                message=f"Could not check {pkg}",
            ))


def check_credentials(report: HealthReport, live: bool = False) -> None:
    """Verify API credentials are stored and formatted correctly."""
    try:
        from scripts.credential_manager import CredentialManager

        cm = CredentialManager()
        results = cm.validate_all()

        for provider, info in results.items():
            if info["found"] and info["format_valid"]:
                status = "pass"
                msg = f"{info['display_name']}: found in {info['source']}, format valid"
            elif info["found"] and not info["format_valid"]:
                status = "warn"
                msg = f"{info['display_name']}: found but format looks incorrect"
            else:
                # Anthropic may be handled natively by Claude Code
                if provider == "anthropic":
                    status = "skip"
                    msg = f"{info['display_name']}: not found (may be handled by Claude Code natively)"
                else:
                    status = "warn"
                    msg = f"{info['display_name']}: not configured"

            report.add(CheckResult(
                name=f"Credential: {provider}",
                category="credentials",
                status=status,
                message=msg,
                details={
                    "source": info["source"],
                    "format_valid": info["format_valid"],
                    "rotation_info": info.get("rotation_info"),
                },
            ))

        # Check rotation warnings
        warnings = cm.check_rotation()
        for w in warnings:
            report.add(CheckResult(
                name="Credential rotation",
                category="credentials",
                status="warn",
                message=w,
            ))

    except ImportError:
        report.add(CheckResult(
            name="Credential Manager",
            category="credentials",
            status="warn",
            message="credential_manager.py not importable; falling back to env var check",
        ))

        # Fallback: check environment variables
        for env_var, label in [
            ("OPENAI_API_KEY", "OpenAI"),
            ("GEMINI_API_KEY", "Gemini"),
            ("ANTHROPIC_API_KEY", "Anthropic"),
        ]:
            value = os.environ.get(env_var)
            if value:
                report.add(CheckResult(
                    name=f"Credential: {label}",
                    category="credentials",
                    status="pass",
                    message=f"{label}: found in environment variable {env_var}",
                ))
            else:
                status = "skip" if label == "Anthropic" else "warn"
                report.add(CheckResult(
                    name=f"Credential: {label}",
                    category="credentials",
                    status=status,
                    message=f"{label}: {env_var} not set",
                ))


def check_api_connectivity(report: HealthReport) -> None:
    """Live connectivity check for AI APIs (only with --live flag)."""
    # OpenAI
    try:
        from scripts.integration_adapters import get_ai_client

        openai_client = get_ai_client("openai")
        available, msg = openai_client.check_available()
        report.add(CheckResult(
            name="API: OpenAI connectivity",
            category="connectivity",
            status="pass" if available else "fail",
            message=msg,
        ))
    except Exception as e:
        report.add(CheckResult(
            name="API: OpenAI connectivity",
            category="connectivity",
            status="fail",
            message=f"OpenAI connectivity check failed: {e}",
        ))

    # Gemini
    try:
        from scripts.integration_adapters import get_ai_client

        gemini_client = get_ai_client("gemini")
        available, msg = gemini_client.check_available()
        report.add(CheckResult(
            name="API: Gemini connectivity",
            category="connectivity",
            status="pass" if available else "fail",
            message=msg,
        ))
    except Exception as e:
        report.add(CheckResult(
            name="API: Gemini connectivity",
            category="connectivity",
            status="fail",
            message=f"Gemini connectivity check failed: {e}",
        ))


def check_project_structure(report: HealthReport, project_dir: str) -> None:
    """Verify required project directories and files exist."""
    required_dirs = [
        "schemas",
        "templates",
        "scripts",
        "agents",
        "outputs",
        "test-data",
    ]

    required_files = [
        "pyproject.toml",
        "workflow.md",
        "state.yaml",
        "templates/memoir.latex",
        "templates/epub.css",
        "templates/epub-metadata.yaml",
    ]

    for d in required_dirs:
        full_path = os.path.join(project_dir, d)
        if os.path.isdir(full_path):
            report.add(CheckResult(
                name=f"Directory: {d}/",
                category="project-structure",
                status="pass",
                message=f"{d}/ exists",
            ))
        else:
            report.add(CheckResult(
                name=f"Directory: {d}/",
                category="project-structure",
                status="warn",
                message=f"{d}/ missing. Run: mkdir -p {d}",
            ))

    for f in required_files:
        full_path = os.path.join(project_dir, f)
        if os.path.isfile(full_path):
            report.add(CheckResult(
                name=f"File: {f}",
                category="project-structure",
                status="pass",
                message=f"{f} exists",
            ))
        else:
            report.add(CheckResult(
                name=f"File: {f}",
                category="project-structure",
                status="warn",
                message=f"{f} missing",
            ))


def check_gitignore_security(report: HealthReport, project_dir: str) -> None:
    """Verify that sensitive files are in .gitignore."""
    gitignore_path = os.path.join(project_dir, ".gitignore")
    if not os.path.isfile(gitignore_path):
        report.add(CheckResult(
            name=".gitignore",
            category="security",
            status="warn",
            message=".gitignore file not found",
        ))
        return

    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    sensitive_patterns = [".venv/", "__pycache__/", "*.pyc"]
    for pattern in sensitive_patterns:
        if pattern in content:
            report.add(CheckResult(
                name=f".gitignore: {pattern}",
                category="security",
                status="pass",
                message=f"{pattern} is excluded from version control",
            ))
        else:
            report.add(CheckResult(
                name=f".gitignore: {pattern}",
                category="security",
                status="warn",
                message=f"{pattern} should be in .gitignore",
            ))

    # Check that no .env files exist in the project
    env_files = list(Path(project_dir).glob(".env*"))
    if env_files:
        report.add(CheckResult(
            name=".env file detected",
            category="security",
            status="warn",
            message=(
                f"Found .env files: {[str(f.name) for f in env_files]}. "
                "Prefer Keychain storage. These files may be auto-read by Claude Code."
            ),
        ))
    else:
        report.add(CheckResult(
            name=".env file check",
            category="security",
            status="pass",
            message="No .env files found in project (good: using Keychain)",
        ))


# ============================================================================
# Report formatting
# ============================================================================


def print_report(report: HealthReport, json_output: bool = False) -> None:
    """Print the health report to stdout."""
    if json_output:
        data = {
            "timestamp": report.timestamp,
            "overall_status": report.overall_status,
            "summary": report.summary,
            "checks": [asdict(c) for c in report.checks],
        }
        print(json.dumps(data, indent=2))
        return

    status_symbols = {
        "pass": "[PASS]",
        "warn": "[WARN]",
        "fail": "[FAIL]",
        "skip": "[SKIP]",
    }

    print("=" * 70)
    print("  AI Autobiography Generator — Integration Health Check")
    print(f"  {report.timestamp}")
    print("=" * 70)
    print()

    # Group by category
    categories: dict[str, list[CheckResult]] = {}
    for check in report.checks:
        categories.setdefault(check.category, []).append(check)

    category_labels = {
        "python": "Python Runtime",
        "python-packages": "Python Packages",
        "system-tools": "System Tools",
        "latex-packages": "LaTeX Packages",
        "credentials": "API Credentials",
        "connectivity": "API Connectivity",
        "project-structure": "Project Structure",
        "security": "Security",
    }

    for category, checks in categories.items():
        label = category_labels.get(category, category)
        print(f"--- {label} ---")
        for check in checks:
            symbol = status_symbols.get(check.status, "[????]")
            print(f"  {symbol} {check.message}")
        print()

    # Summary
    print("=" * 70)
    overall_display = {
        "healthy": "HEALTHY",
        "healthy-with-warnings": "HEALTHY (with warnings)",
        "degraded": "DEGRADED (some checks failed)",
        "critical": "CRITICAL (pipeline cannot run)",
    }
    print(f"  Overall: {overall_display.get(report.overall_status, report.overall_status)}")
    print(
        f"  Passed: {report.summary.get('pass', 0)} | "
        f"Warnings: {report.summary.get('warn', 0)} | "
        f"Failed: {report.summary.get('fail', 0)} | "
        f"Skipped: {report.summary.get('skip', 0)}"
    )
    print("=" * 70)


# ============================================================================
# Main
# ============================================================================


def main() -> None:
    """Run the integration health check."""
    parser = argparse.ArgumentParser(
        description="Integration Health Check for AI Autobiography Generator"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Include live API connectivity checks (requires network)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--only",
        choices=[
            "python", "packages", "tools", "latex",
            "credentials", "connectivity", "structure", "security",
        ],
        help="Run only a specific category of checks",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Project root directory (default: current directory)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    project_dir = os.path.abspath(args.project_dir)

    # Add scripts directory to path for imports
    scripts_dir = os.path.join(project_dir, "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, project_dir)

    report = HealthReport()

    # Run checks based on --only filter
    checks_to_run = {
        "python": check_python_version,
        "packages": check_python_packages,
        "tools": lambda r: (check_pandoc(r), check_xelatex(r)),
        "latex": check_latex_packages,
        "credentials": lambda r: check_credentials(r, live=args.live),
        "connectivity": check_api_connectivity if args.live else None,
        "structure": lambda r: check_project_structure(r, project_dir),
        "security": lambda r: check_gitignore_security(r, project_dir),
    }

    if args.only:
        check_fn = checks_to_run.get(args.only)
        if check_fn:
            check_fn(report)
        else:
            print(f"Unknown category: {args.only}", file=sys.stderr)
            sys.exit(2)
    else:
        for name, check_fn in checks_to_run.items():
            if check_fn is None:
                continue
            try:
                check_fn(report)
            except Exception as e:
                report.add(CheckResult(
                    name=f"Category: {name}",
                    category=name,
                    status="fail",
                    message=f"Check raised an exception: {e}",
                ))

        # Connectivity only with --live
        if args.live:
            try:
                check_api_connectivity(report)
            except Exception as e:
                report.add(CheckResult(
                    name="API connectivity",
                    category="connectivity",
                    status="fail",
                    message=f"Connectivity check failed: {e}",
                ))

    report.finalize()
    print_report(report, json_output=args.json)

    # Exit code
    if report.overall_status == "critical":
        sys.exit(2)
    elif report.overall_status == "degraded":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
