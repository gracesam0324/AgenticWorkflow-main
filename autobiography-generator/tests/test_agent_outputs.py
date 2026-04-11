"""Agent output format compliance tests.

Tests verify:
- Each agent .md file has valid YAML frontmatter (name, description, model, tools)
- reviewer.md exists (may be created later — skips gracefully)
- translator.md exists and does NOT contain 'memory: project'
- orchestrator.md exists with maxTurns >= 100
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

AGENTS_DIR = Path(__file__).parent.parent / ".claude" / "agents"

REQUIRED_FRONTMATTER_KEYS = {"name", "description", "model", "tools"}


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _parse_frontmatter(filepath: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file.

    Frontmatter is delimited by '---' lines at the top of the file.
    Returns the parsed dict, or None if no valid frontmatter found.
    """
    text = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def _get_agent_files() -> list[Path]:
    """List all .md files in the agents directory."""
    if not AGENTS_DIR.is_dir():
        return []
    return sorted(AGENTS_DIR.glob("*.md"))


# ──────────────────────────────────────────────
# Frontmatter Validation for All Agents
# ──────────────────────────────────────────────


class TestAgentFrontmatter:
    """Every agent .md file must have valid frontmatter with required keys."""

    def test_agents_directory_exists(self):
        """The .claude/agents/ directory exists."""
        assert AGENTS_DIR.is_dir(), f"Agents directory not found at {AGENTS_DIR}"

    def test_at_least_one_agent_file(self):
        """At least one agent .md file exists."""
        agents = _get_agent_files()
        assert len(agents) > 0, "No agent .md files found"

    @pytest.mark.parametrize("agent_file", _get_agent_files(), ids=lambda p: p.name)
    def test_frontmatter_exists(self, agent_file: Path):
        """Agent file has YAML frontmatter delimited by '---'."""
        fm = _parse_frontmatter(agent_file)
        assert fm is not None, f"{agent_file.name} has no valid YAML frontmatter"

    @pytest.mark.parametrize("agent_file", _get_agent_files(), ids=lambda p: p.name)
    def test_frontmatter_has_name(self, agent_file: Path):
        """Agent frontmatter contains 'name' field."""
        fm = _parse_frontmatter(agent_file)
        assert fm is not None, f"{agent_file.name} has no frontmatter"
        assert "name" in fm, f"{agent_file.name} frontmatter missing 'name'"
        assert isinstance(fm["name"], str) and len(fm["name"]) > 0

    @pytest.mark.parametrize("agent_file", _get_agent_files(), ids=lambda p: p.name)
    def test_frontmatter_has_description(self, agent_file: Path):
        """Agent frontmatter contains 'description' field."""
        fm = _parse_frontmatter(agent_file)
        assert fm is not None
        assert "description" in fm, f"{agent_file.name} frontmatter missing 'description'"
        assert isinstance(fm["description"], str) and len(fm["description"]) > 0

    @pytest.mark.parametrize("agent_file", _get_agent_files(), ids=lambda p: p.name)
    def test_frontmatter_has_model(self, agent_file: Path):
        """Agent frontmatter contains 'model' field."""
        fm = _parse_frontmatter(agent_file)
        assert fm is not None
        assert "model" in fm, f"{agent_file.name} frontmatter missing 'model'"
        assert fm["model"] in ("opus", "sonnet", "haiku"), (
            f"{agent_file.name} has unexpected model: {fm['model']}"
        )

    @pytest.mark.parametrize("agent_file", _get_agent_files(), ids=lambda p: p.name)
    def test_frontmatter_has_tools(self, agent_file: Path):
        """Agent frontmatter contains 'tools' field."""
        fm = _parse_frontmatter(agent_file)
        assert fm is not None
        assert "tools" in fm, f"{agent_file.name} frontmatter missing 'tools'"
        # tools can be a list or a comma-separated string
        tools = fm["tools"]
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",")]
        assert isinstance(tools, list) and len(tools) > 0

    @pytest.mark.parametrize("agent_file", _get_agent_files(), ids=lambda p: p.name)
    def test_frontmatter_name_matches_filename(self, agent_file: Path):
        """Agent frontmatter 'name' matches the filename (without .md)."""
        fm = _parse_frontmatter(agent_file)
        assert fm is not None
        expected_name = agent_file.stem  # e.g., "orchestrator", "chapter-writer"
        assert fm["name"] == expected_name, (
            f"{agent_file.name}: frontmatter name '{fm['name']}' "
            f"does not match filename stem '{expected_name}'"
        )


# ──────────────────────────────────────────────
# Specific Agent Existence and Constraints
# ──────────────────────────────────────────────


class TestReviewerAgent:
    """Tests for reviewer.md."""

    def test_reviewer_exists(self):
        """reviewer.md exists in the agents directory."""
        reviewer_path = AGENTS_DIR / "reviewer.md"
        if not reviewer_path.exists():
            pytest.skip("reviewer.md not yet created (Phase B dependency)")
        assert reviewer_path.exists()

    def test_reviewer_has_valid_frontmatter(self):
        """reviewer.md has valid frontmatter with required keys."""
        reviewer_path = AGENTS_DIR / "reviewer.md"
        if not reviewer_path.exists():
            pytest.skip("reviewer.md not yet created")
        fm = _parse_frontmatter(reviewer_path)
        assert fm is not None
        for key in REQUIRED_FRONTMATTER_KEYS:
            assert key in fm, f"reviewer.md frontmatter missing '{key}'"


class TestTranslatorAgent:
    """Tests for translator.md — must exist and must NOT contain 'memory: project'."""

    def test_translator_exists(self):
        """translator.md exists in the agents directory."""
        translator_path = AGENTS_DIR / "translator.md"
        assert translator_path.exists(), f"translator.md not found at {translator_path}"

    def test_translator_has_valid_frontmatter(self):
        """translator.md has valid frontmatter with required keys."""
        translator_path = AGENTS_DIR / "translator.md"
        assert translator_path.exists()
        fm = _parse_frontmatter(translator_path)
        assert fm is not None, "translator.md has no valid YAML frontmatter"
        for key in REQUIRED_FRONTMATTER_KEYS:
            assert key in fm, f"translator.md frontmatter missing '{key}'"

    def test_translator_no_memory_project(self):
        """translator.md frontmatter does NOT contain 'memory: project' (section 21.5).

        The parent project's translator.md has 'memory: project' which gives
        access to the parent's project memory. The child project must NOT
        inherit this — it would cause the translator to load irrelevant
        parent project context.
        """
        translator_path = AGENTS_DIR / "translator.md"
        assert translator_path.exists()
        fm = _parse_frontmatter(translator_path)
        assert fm is not None
        assert fm.get("memory") != "project", (
            "translator.md must NOT contain 'memory: project' — "
            "removed per section 21.5 to prevent parent project memory leakage"
        )

    def test_translator_no_memory_project_in_raw_text(self):
        """Double-check: 'memory: project' does not appear anywhere in translator.md."""
        translator_path = AGENTS_DIR / "translator.md"
        assert translator_path.exists()
        content = translator_path.read_text(encoding="utf-8")
        # Check only in the frontmatter section, not in documentation text
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        assert match is not None
        frontmatter_text = match.group(1)
        assert "memory:" not in frontmatter_text, (
            "translator.md frontmatter contains a 'memory' key — must be removed"
        )

    def test_translator_preserves_7_step_protocol(self):
        """translator.md preserves the 7-step translation protocol."""
        translator_path = AGENTS_DIR / "translator.md"
        assert translator_path.exists()
        content = translator_path.read_text(encoding="utf-8")

        # Verify all 7 steps are present
        expected_steps = [
            "Step 1",  # Load Terminology Glossary
            "Step 2",  # Read English Source
            "Step 3",  # Translate
            "Step 4",  # Self-Review + Translation pACS
            "Step 5",  # Update Glossary
            "Step 6",  # Write Translation Output
            "Step 7",  # Write Translation pACS Log
        ]
        for step in expected_steps:
            assert step in content, f"translator.md missing '{step}' in protocol"


class TestOrchestratorAgent:
    """Tests for orchestrator.md — must exist with maxTurns >= 100."""

    def test_orchestrator_exists(self):
        """orchestrator.md exists in the agents directory."""
        orchestrator_path = AGENTS_DIR / "orchestrator.md"
        assert orchestrator_path.exists(), f"orchestrator.md not found at {orchestrator_path}"

    def test_orchestrator_has_valid_frontmatter(self):
        """orchestrator.md has valid frontmatter with required keys."""
        orchestrator_path = AGENTS_DIR / "orchestrator.md"
        fm = _parse_frontmatter(orchestrator_path)
        assert fm is not None, "orchestrator.md has no valid YAML frontmatter"
        for key in REQUIRED_FRONTMATTER_KEYS:
            assert key in fm, f"orchestrator.md frontmatter missing '{key}'"

    def test_orchestrator_max_turns_sufficient(self):
        """orchestrator.md maxTurns >= 100 (complex multi-phase coordination)."""
        orchestrator_path = AGENTS_DIR / "orchestrator.md"
        fm = _parse_frontmatter(orchestrator_path)
        assert fm is not None
        assert "maxTurns" in fm, "orchestrator.md frontmatter missing 'maxTurns'"
        assert fm["maxTurns"] >= 100, (
            f"orchestrator.md maxTurns is {fm['maxTurns']}, must be >= 100 "
            f"for complex multi-phase coordination"
        )

    def test_orchestrator_has_agent_tool(self):
        """orchestrator.md tools include 'Agent' for spawning subagents."""
        orchestrator_path = AGENTS_DIR / "orchestrator.md"
        fm = _parse_frontmatter(orchestrator_path)
        assert fm is not None
        tools = fm.get("tools", [])
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",")]
        assert "Agent" in tools, (
            f"orchestrator.md tools {tools} must include 'Agent' for subagent spawning"
        )


# ──────────────────────────────────────────────
# Reviewer-Deep Agent
# ──────────────────────────────────────────────


class TestReviewerDeepAgent:
    """Tests for reviewer-deep.md."""

    def test_reviewer_deep_exists(self):
        """reviewer-deep.md exists in the agents directory."""
        path = AGENTS_DIR / "reviewer-deep.md"
        assert path.exists(), f"reviewer-deep.md not found at {path}"

    def test_reviewer_deep_has_valid_frontmatter(self):
        """reviewer-deep.md has valid frontmatter with required keys."""
        path = AGENTS_DIR / "reviewer-deep.md"
        fm = _parse_frontmatter(path)
        assert fm is not None, "reviewer-deep.md has no valid YAML frontmatter"
        for key in REQUIRED_FRONTMATTER_KEYS:
            assert key in fm, f"reviewer-deep.md frontmatter missing '{key}'"

    def test_reviewer_deep_is_read_only(self):
        """reviewer-deep.md tools do NOT include Write or Edit (read-only agent)."""
        path = AGENTS_DIR / "reviewer-deep.md"
        fm = _parse_frontmatter(path)
        assert fm is not None
        tools = fm.get("tools", [])
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",")]
        assert "Write" not in tools, "reviewer-deep must be read-only (no Write tool)"
        assert "Edit" not in tools, "reviewer-deep must be read-only (no Edit tool)"
