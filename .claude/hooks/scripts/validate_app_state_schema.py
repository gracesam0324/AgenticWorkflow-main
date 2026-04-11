#!/usr/bin/env python3
"""Infrastructure-level: Validate app-state.json against a JSON schema.

Usage: python validate_app_state_schema.py --schema <schema_file> --data <data_file>
Outputs JSON with validation results.
"""
import argparse
import json
import os
import sys


def validate_type(value, expected_type):
    """Validate a value matches the expected JSON schema type."""
    type_map = {
        "string": str, "number": (int, float), "integer": int,
        "boolean": bool, "array": list, "object": dict, "null": type(None),
    }
    expected = type_map.get(expected_type)
    if expected is None:
        return True
    return isinstance(value, expected)


def validate_against_schema(data, schema, path=""):
    """Validate data against a JSON schema. Returns list of errors."""
    errors = []

    schema_type = schema.get("type")
    if schema_type and not validate_type(data, schema_type):
        errors.append(f"{path or 'root'}: expected type '{schema_type}', got '{type(data).__name__}'")
        return errors

    if schema_type == "object":
        required = schema.get("required", [])
        for req in required:
            if req not in data:
                errors.append(f"{path}.{req}: required field missing")

        properties = schema.get("properties", {})
        for key, prop_schema in properties.items():
            if key in data:
                errors.extend(validate_against_schema(data[key], prop_schema, f"{path}.{key}"))

    if schema_type == "array":
        items_schema = schema.get("items", {})
        if isinstance(data, list):
            for i, item in enumerate(data):
                errors.extend(validate_against_schema(item, items_schema, f"{path}[{i}]"))

    if "enum" in schema:
        if data not in schema["enum"]:
            errors.append(f"{path or 'root'}: value '{data}' not in enum {schema['enum']}")

    if "minimum" in schema and isinstance(data, (int, float)):
        if data < schema["minimum"]:
            errors.append(f"{path or 'root'}: {data} < minimum {schema['minimum']}")

    if "maxLength" in schema and isinstance(data, str):
        if len(data) > schema["maxLength"]:
            errors.append(f"{path or 'root'}: length {len(data)} > maxLength {schema['maxLength']}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate app-state.json against schema")
    parser.add_argument("--schema", required=True, help="Path to JSON schema file")
    parser.add_argument("--data", required=True, help="Path to data file to validate")
    args = parser.parse_args()

    try:
        with open(args.schema, "r", encoding="utf-8") as f:
            schema = json.load(f)
        with open(args.data, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(json.dumps({"valid": False, "errors": [f"File not found: {e.filename}"]}))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({"valid": False, "errors": [f"Invalid JSON: {str(e)}"]}))
        sys.exit(1)

    errors = validate_against_schema(data, schema)
    result = {"valid": len(errors) == 0, "errors": errors, "fields_checked": len(schema.get("properties", {}))}
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
