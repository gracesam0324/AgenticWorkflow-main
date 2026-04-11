#!/usr/bin/env python3
"""
Schema Validator — Central JSON Schema validation for all autobiography artifacts.

Usage:
    python3 scripts/schema_validator.py --schema schemas/interview_transcript.schema.json --data outputs/interviews/INT-001.json
    python3 scripts/schema_validator.py --schema schemas/story_bible.schema.json --data outputs/story-bible/story_bible.json
    python3 scripts/schema_validator.py --schema schemas/chapter_draft.schema.json --data outputs/chapters/ch01_draft_v1.meta.json
    python3 scripts/schema_validator.py --schema schemas/review_verdict.schema.json --data review-logs/RV-001.json

Output: JSON to stdout
    {"valid": true, "errors": [], "warnings": []}

Exit codes:
    0 — validation completed (check "valid" field)
    1 — file not found or argument error
    2 — schema itself is invalid

P1 Compliance: All validation is deterministic — no AI inference.
SOT Compliance: Read-only — no file writes.
"""

import argparse
import json
import os
import sys
from typing import Any


def load_json_file(path: str) -> dict[str, Any] | None:
    """Load and parse a JSON file. Returns None on failure."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def validate_json_schema(schema: dict, data: dict) -> tuple[bool, list[str], list[str]]:
    """
    Validate data against a JSON Schema.

    Uses jsonschema library if available; falls back to manual structural
    validation for environments without pip packages installed.

    Returns:
        (is_valid, errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        import jsonschema
        from jsonschema import Draft202012Validator, ValidationError

        validator = Draft202012Validator(schema)
        validation_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))

        for error in validation_errors:
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            msg = f"[{path}] {error.message}"

            # Classify severity: required fields and type mismatches are errors;
            # pattern/format violations are warnings
            if error.validator in ("required", "type", "const", "enum"):
                errors.append(msg)
            elif error.validator in ("minItems", "minLength", "minimum", "maximum"):
                errors.append(msg)
            else:
                warnings.append(msg)

        return len(errors) == 0, errors, warnings

    except ImportError:
        # Fallback: manual structural validation
        return _manual_validate(schema, data, errors, warnings)


def _manual_validate(
    schema: dict, data: dict, errors: list[str], warnings: list[str], path: str = ""
) -> tuple[bool, list[str], list[str]]:
    """
    Manual structural validation when jsonschema is not installed.
    Covers: required, type, enum, const, minLength, minItems, minimum, maximum, pattern.
    """
    schema_type = schema.get("type")

    # Type check
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "null": type(None),
    }

    if schema_type and schema_type in type_map:
        expected = type_map[schema_type]
        if not isinstance(data, expected):
            # Special case: integer also satisfies number
            if not (schema_type == "number" and isinstance(data, (int, float))):
                errors.append(f"[{path or '(root)'}] Expected type '{schema_type}', got '{type(data).__name__}'")
                return False, errors, warnings

    # Const
    if "const" in schema and data != schema["const"]:
        errors.append(f"[{path}] Expected const value '{schema['const']}', got '{data}'")

    # Enum
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"[{path}] Value '{data}' not in enum {schema['enum']}")

    # String constraints
    if isinstance(data, str):
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(f"[{path}] String too short: {len(data)} < {schema['minLength']}")
        if "pattern" in schema:
            import re
            if not re.match(schema["pattern"], data):
                warnings.append(f"[{path}] String '{data}' does not match pattern '{schema['pattern']}'")

    # Numeric constraints
    if isinstance(data, (int, float)):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"[{path}] Value {data} below minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"[{path}] Value {data} above maximum {schema['maximum']}")

    # Array constraints
    if isinstance(data, list):
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(f"[{path}] Array has {len(data)} items, minimum is {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(data):
                _manual_validate(schema["items"], item, errors, warnings, f"{path}[{i}]")

    # Object constraints
    if isinstance(data, dict):
        # Required fields
        for req in schema.get("required", []):
            if req not in data:
                errors.append(f"[{path}] Missing required field: '{req}'")

        # Validate known properties
        properties = schema.get("properties", {})
        for key, prop_schema in properties.items():
            if key in data:
                _manual_validate(prop_schema, data[key], errors, warnings, f"{path}.{key}" if path else key)

    return len(errors) == 0, errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate JSON data against a JSON Schema")
    parser.add_argument("--schema", required=True, help="Path to JSON Schema file")
    parser.add_argument("--data", required=True, help="Path to JSON data file to validate")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    # Load schema
    schema = load_json_file(args.schema)
    if schema is None:
        print(json.dumps({"valid": False, "error": f"Schema file not found or invalid: {args.schema}"}))
        sys.exit(1)

    # Load data
    data = load_json_file(args.data)
    if data is None:
        print(json.dumps({"valid": False, "error": f"Data file not found or invalid JSON: {args.data}"}))
        sys.exit(1)

    # Validate
    is_valid, errors, warnings = validate_json_schema(schema, data)

    if args.strict and warnings:
        is_valid = False
        errors.extend([f"[strict] {w}" for w in warnings])

    result = {
        "valid": is_valid,
        "schema": args.schema,
        "data": args.data,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
