#!/usr/bin/env python3
"""
PreToolUse Hook — Schema Validation on Write

Triggered before Write/Edit operations on JSON files in schemas-governed directories.
Validates that the file about to be written conforms to the appropriate JSON Schema.

Exit codes:
    0 — allow (file passes validation or is not schema-governed)
    2 — deny (file violates schema — blocks the write)

Environment variables (from Claude Code hooks):
    CLAUDE_TOOL_INPUT — JSON with "file_path" and "content" fields
"""

import json
import os
import sys


# Map output directories to their governing schemas
SCHEMA_MAP = {
    "outputs/interviews/": "schemas/interview_transcript.schema.json",
    "outputs/story-bible/story_bible.json": "schemas/story_bible.schema.json",
    "outputs/chapters/": "schemas/chapter_draft.schema.json",  # for .meta.json files
    "review-logs/": "schemas/review_verdict.schema.json",
}


def get_schema_for_file(file_path: str, project_dir: str) -> str | None:
    """Determine which schema governs a given file path."""
    rel_path = os.path.relpath(file_path, project_dir)

    # Only validate JSON files
    if not rel_path.endswith(".json"):
        return None

    # Skip non-metadata chapter files
    if "outputs/chapters/" in rel_path and not rel_path.endswith(".meta.json"):
        return None

    for path_prefix, schema_file in SCHEMA_MAP.items():
        if rel_path.startswith(path_prefix) or rel_path == path_prefix:
            schema_path = os.path.join(project_dir, schema_file)
            if os.path.isfile(schema_path):
                return schema_path

    return None


def main():
    repo_root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    project_dir = os.path.join(repo_root, "autobiography-generator")
    tool_input_raw = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    try:
        tool_input = json.loads(tool_input_raw)
    except json.JSONDecodeError:
        sys.exit(0)  # Cannot parse input — allow

    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    if not file_path:
        sys.exit(0)

    # Resolve to absolute path
    if not os.path.isabs(file_path):
        file_path = os.path.join(project_dir, file_path)

    schema_path = get_schema_for_file(file_path, project_dir)
    if schema_path is None:
        sys.exit(0)  # No schema governs this file

    # Try to parse the content as JSON
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        # Content is not JSON — might be a markdown write; allow
        sys.exit(0)

    # Load schema
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except (json.JSONDecodeError, OSError):
        print(f"WARNING: Could not load schema {schema_path} — allowing write", file=sys.stderr)
        sys.exit(0)

    # Validate
    sys.path.insert(0, os.path.join(project_dir, "scripts"))
    try:
        from schema_validator import validate_json_schema
        is_valid, errors, warnings = validate_json_schema(schema, data)
    except ImportError:
        # Fallback: basic structural check
        is_valid = True
        errors = []

    if not is_valid:
        error_msg = (
            f"SCHEMA VALIDATION FAILED — blocking write to {os.path.relpath(file_path, project_dir)}\n"
            f"Schema: {os.path.relpath(schema_path, project_dir)}\n"
            f"Errors ({len(errors)}):\n"
        )
        for err in errors[:10]:  # Cap at 10 errors
            error_msg += f"  - {err}\n"
        if len(errors) > 10:
            error_msg += f"  ... and {len(errors) - 10} more errors\n"
        error_msg += "\nFix the data to conform to the schema before writing."

        print(error_msg, file=sys.stderr)
        sys.exit(2)  # Deny the write

    # If only warnings, allow but inform
    if warnings:
        warn_msg = f"Schema warnings for {os.path.relpath(file_path, project_dir)}:\n"
        for w in warnings[:5]:
            warn_msg += f"  - {w}\n"
        print(warn_msg, file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
