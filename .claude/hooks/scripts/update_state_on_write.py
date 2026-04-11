#!/usr/bin/env python3
"""
PostToolUse Hook — State Update on Write

Triggered after Write/Edit operations to automatically update .claude/state.yaml
when key artifacts are created or modified.

Tracks:
- Interview transcript additions (updates interviews.total_sessions)
- Story bible modifications (updates story_bible.version)
- Chapter draft creation/revision (updates chapters.ch-N.status)
- Review verdict creation (updates chapters.ch-N.review_rounds)

Exit codes:
    0 — always (informational hook, never blocks)

SOT Compliance: Only THIS script writes to state.yaml (Orchestrator delegate).
"""

import json
import os
import re
import sys
from datetime import date


def load_yaml_simple(path: str) -> dict | None:
    """Load a YAML file using simple line-by-line parsing.

    Handles the flat/shallow structure of state.yaml without requiring PyYAML.
    For complex nested YAML, falls back to PyYAML if available.
    """
    if not os.path.isfile(path):
        return None
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        # Minimal YAML parser for state.yaml structure
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # If content looks complex, return a basic dict
            return {"_raw": content, "_parsed": False}
        except OSError:
            return None


def save_yaml_simple(path: str, data: dict) -> None:
    """Write state data back to YAML."""
    try:
        import yaml
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except ImportError:
        # Write a JSON-like representation as YAML
        with open(path, "w", encoding="utf-8") as f:
            f.write("# state.yaml — Auto-updated by update_state_on_write.py\n")
            f.write(f"# Last updated: {date.today().isoformat()}\n\n")
            f.write(json.dumps(data, indent=2, ensure_ascii=False))


def detect_artifact_type(file_path: str) -> tuple[str | None, dict]:
    """Determine what kind of artifact was written and extract relevant info."""
    basename = os.path.basename(file_path)
    rel_parts = file_path.replace("\\", "/").split("/")

    # Interview transcript
    if "interviews" in rel_parts and basename.endswith(".json"):
        m = re.match(r"(INT-\d{3})\.json", basename, re.IGNORECASE)
        session_id = m.group(1).upper() if m else basename.replace(".json", "")
        return "interview", {"session_id": session_id}

    # Story bible
    if basename == "story_bible.json":
        return "story_bible", {}

    # Chapter draft (prose)
    m = re.match(r"ch(\d{2})_draft_v(\d+)\.md$", basename)
    if m:
        return "chapter_prose", {"chapter": int(m.group(1)), "version": int(m.group(2))}

    # Chapter metadata
    m = re.match(r"ch(\d{2})_draft_v(\d+)\.meta\.json$", basename)
    if m:
        return "chapter_meta", {"chapter": int(m.group(1)), "version": int(m.group(2))}

    # Review verdict
    if "review-logs" in rel_parts and basename.endswith(".json"):
        return "review", {"filename": basename}

    return None, {}


def update_state(state: dict, artifact_type: str, info: dict, file_path: str) -> bool:
    """Update the state dict based on artifact type. Returns True if modified."""
    workflow = state.get("workflow", state)  # Handle both wrapped and unwrapped
    modified = False

    if artifact_type == "interview":
        interviews = workflow.setdefault("interviews", {
            "total_sessions": 0,
            "total_segments": 0,
            "sessions_processed": [],
        })
        session_id = info["session_id"]
        if session_id not in interviews.get("sessions_processed", []):
            interviews.setdefault("sessions_processed", []).append(session_id)
            interviews["total_sessions"] = len(interviews["sessions_processed"])
            modified = True

    elif artifact_type == "story_bible":
        sb = workflow.setdefault("story_bible", {
            "path": "outputs/story-bible/story_bible.json",
            "version": 0,
            "character_count": 0,
            "event_count": 0,
            "validated": False,
        })
        sb["version"] = sb.get("version", 0) + 1
        sb["validated"] = False  # Reset until explicitly validated
        modified = True

        # Try to read actual counts
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sb_data = json.load(f)
            sb["character_count"] = len(sb_data.get("characters", []))
            sb["event_count"] = len(sb_data.get("timeline", []))
        except (json.JSONDecodeError, OSError):
            pass

    elif artifact_type in ("chapter_prose", "chapter_meta"):
        ch_num = info["chapter"]
        version = info["version"]
        chapters = workflow.setdefault("chapters", {})
        ch_key = f"ch-{ch_num}"
        ch_state = chapters.setdefault(ch_key, {
            "status": "not_started",
            "draft_version": 0,
            "word_count": 0,
            "review_rounds": 0,
            "output_path": "",
        })

        if artifact_type == "chapter_prose":
            ch_state["status"] = "drafted"
            ch_state["draft_version"] = version
            ch_state["output_path"] = file_path
            # Estimate word count from file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                ch_state["word_count"] = len(text.split())
            except OSError:
                pass

        elif artifact_type == "chapter_meta":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                ch_state["word_count"] = meta.get("meta", {}).get("word_count", ch_state.get("word_count", 0))
            except (json.JSONDecodeError, OSError):
                pass

        modified = True

    elif artifact_type == "review":
        # Try to determine which chapter was reviewed
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                review = json.load(f)
            artifact_path = review.get("meta", {}).get("artifact_path", "")
            m = re.search(r"ch(\d{2})", artifact_path)
            if m:
                ch_num = int(m.group(1))
                ch_key = f"ch-{ch_num}"
                chapters = workflow.setdefault("chapters", {})
                ch_state = chapters.setdefault(ch_key, {"review_rounds": 0})
                ch_state["review_rounds"] = ch_state.get("review_rounds", 0) + 1
                ch_state["status"] = "reviewed"

                reviewer_pacs = review.get("pacs", {}).get("reviewer_score")
                if reviewer_pacs is not None:
                    ch_state["last_reviewer_pacs"] = reviewer_pacs

                verdict = review.get("verdict", {}).get("result")
                if verdict == "PASS":
                    ch_state["status"] = "approved"

                ch_state["review_path"] = file_path
                modified = True
        except (json.JSONDecodeError, OSError):
            pass

    return modified


def main():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    tool_input_raw = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    try:
        tool_input = json.loads(tool_input_raw)
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    if not os.path.isabs(file_path):
        file_path = os.path.join(project_dir, file_path)

    # Detect what was written
    artifact_type, info = detect_artifact_type(file_path)
    if artifact_type is None:
        sys.exit(0)  # Not a tracked artifact

    # Load current state
    state_path = os.path.join(project_dir, ".claude", "state.yaml")
    state = load_yaml_simple(state_path)

    if state is None or state.get("_parsed") is False:
        # Initialize state — MUST include orchestration section (v2.0)
        state = {
            "workflow": {
                "name": "AI Autobiography Generator",
                "current_step": 1,
                "status": "in_progress",
                "parent_genome": {
                    "source": "AgenticWorkflow",
                    "version": date.today().isoformat(),
                    "inherited_dna": [
                        "absolute-criteria", "sot-pattern", "3-phase-structure",
                        "4-layer-qa", "safety-hooks", "adversarial-review",
                        "decision-log", "context-preservation",
                    ],
                },
                "outputs": {},
                "book_config": {
                    "subject_name": "",
                    "total_chapters": 0,
                    "target_word_count": 0,
                },
            },
            "orchestration": {
                "version": "2.0",
                "current_phase": "build",
                "current_substep": None,
                "teams": {},
                "tasks": {"total": 0, "completed": 0, "failed": 0, "blocked": 0, "items": {}},
                "fallback": {"activations": [], "current_tier": 2},
                "rlm": {"last_snapshot": "", "knowledge_archive_path": "",
                         "session_count": 0, "recovery_points": []},
                "translation": {"status": "active", "glossary_path": "translations/glossary.yaml",
                                "glossary_terms_count": 34, "total_translations": 0,
                                "completed_translations": 0, "pacs_history": {},
                                "pending_translations": [], "pairs": {}},
                "error_log": [],
            },
        }

    # Update state
    modified = update_state(state, artifact_type, info, file_path)

    if modified:
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        save_yaml_simple(state_path, state)
        print(f"State updated: {artifact_type} — {info}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
