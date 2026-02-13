from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class SchemaValidationError(ValueError):
    """Raised when payload fails schema validation."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_schema(schema_path: str) -> dict[str, Any]:
    path = _repo_root() / schema_path
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_payload(payload: Any, schema_path: str) -> None:
    schema = load_schema(schema_path)
    errors: list[str] = []
    _validate_node(payload, schema, "$", errors)
    if errors:
        raise SchemaValidationError(f"Schema validation failed for {schema_path}: {'; '.join(errors)}")


def _validate_node(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    expected_type = schema.get("type")
    if expected_type:
        _validate_type(value, expected_type, path, errors)
        if errors and path in errors[-1]:
            return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength {schema['minLength']}")
        _validate_format(value, schema.get("format"), path, errors)

    if isinstance(value, (int, float)):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: value below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: value above maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: value not above exclusiveMinimum {schema['exclusiveMinimum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: list shorter than minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: list longer than maxItems {schema['maxItems']}")
        if schema.get("uniqueItems") and len(set(map(str, value))) != len(value):
            errors.append(f"{path}: list items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_node(item, item_schema, f"{path}[{index}]", errors)

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra_keys = set(value).difference(properties)
            if extra_keys:
                errors.append(f"{path}: additional properties not allowed: {sorted(extra_keys)}")
        for key, prop_schema in properties.items():
            if key in value and isinstance(prop_schema, dict):
                _validate_node(value[key], prop_schema, f"{path}.{key}", errors)


def _validate_format(value: str, fmt: str | None, path: str, errors: list[str]) -> None:
    if fmt == "date-time":
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{path}: invalid date-time format")
    elif fmt == "uri":
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{path}: invalid uri format")
    elif fmt == "email":
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            errors.append(f"{path}: invalid email format")


def _validate_type(value: Any, expected_type: str, path: str, errors: list[str]) -> None:
    checks = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
        "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
        "boolean": lambda x: isinstance(x, bool),
    }
    check = checks.get(expected_type)
    if check and not check(value):
        errors.append(f"{path}: expected {expected_type}, got {type(value).__name__}")
