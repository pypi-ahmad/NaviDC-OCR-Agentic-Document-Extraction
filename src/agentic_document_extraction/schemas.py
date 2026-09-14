"""JSON Schema compilation, validation, and OpenAI Structured Outputs adaptation.

This module validates extraction schemas against a strict JSON Schema keyword
whitelist, compiles flattened UI form rows into nested schemas, computes
canonical SHA-256 schema hashes, and adapts user schemas into strict nullable
schemas for OpenAI structured outputs. It must not execute OCR or run model
extractions. Open validation.py next to see how records are validated against
these schemas.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from .models import SchemaDefinition

# Guard limits: prevent oversized schemas or excessive recursion from exhausting
# LLM prompt token windows or triggering stack overflows.
MAX_SCHEMA_BYTES = 1024 * 1024
MAX_FIELD_GUIDE_BYTES = 256 * 1024
MAX_LEAF_FIELDS = 100
MAX_SCHEMA_DEPTH = 8

_ALLOWED_KEYS = {
    "$schema",
    "title",
    "description",
    "type",
    "properties",
    "items",
    "required",
    "additionalProperties",
    "enum",
    "pattern",
    "format",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "x-alternativeNames",
    "x-validation-rules",
}
_PRIMITIVE_TYPES = {"string", "number", "integer", "boolean"}
_PATH_PART = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*(\[\])?$")


class SchemaError(ValueError):
    """Raised for an unsafe or unsupported extraction schema."""


SCHEMA_TEMPLATES: dict[str, dict[str, Any]] = {
    "Generic form": {
        "title": "Generic form",
        "type": "object",
        "properties": {
            "document_title": {"type": "string", "description": "Visible document title"},
            "reference_number": {
                "type": "string",
                "description": "Primary visible reference or identifier",
            },
            "date": {"type": "string", "format": "date", "description": "Document date"},
        },
        "required": [],
        "additionalProperties": False,
    },
    "Invoice": {
        "title": "Invoice",
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string", "x-alternativeNames": ["invoice", "invoice no"]},
            "invoice_date": {"type": "string", "format": "date"},
            "vendor": {"type": "string"},
            "customer": {"type": "string"},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["description", "amount"],
                    "additionalProperties": False,
                },
            },
            "total": {"type": "number"},
        },
        "required": ["invoice_number", "total"],
        "additionalProperties": False,
        "x-validation-rules": [
            {
                "type": "sum_items_equals",
                "target": "/total",
                "items": "/line_items",
                "value": "/amount",
                "tolerance": 0.01,
            }
        ],
    },
    "Receipt": {
        "title": "Receipt",
        "type": "object",
        "properties": {
            "merchant": {"type": "string"},
            "date": {"type": "string", "format": "date"},
            "subtotal": {"type": "number"},
            "tax": {"type": "number"},
            "total": {"type": "number"},
        },
        "required": ["merchant", "total"],
        "additionalProperties": False,
        "x-validation-rules": [
            {
                "type": "sum_fields_equals",
                "target": "/total",
                "fields": ["/subtotal", "/tax"],
                "tolerance": 0.01,
            }
        ],
    },
    "Prior authorization": {
        "title": "Prior authorization",
        "type": "object",
        "properties": {
            "member": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "member_id": {"type": "string"},
                    "date_of_birth": {"type": "string", "format": "date"},
                },
                "required": ["member_id"],
                "additionalProperties": False,
            },
            "provider_name": {"type": "string"},
            "npi": {"type": "string", "pattern": "^[0-9]{10}$"},
            "diagnosis_codes": {"type": "array", "items": {"type": "string"}},
            "procedure_codes": {"type": "array", "items": {"type": "string"}},
            "service_start_date": {"type": "string", "format": "date"},
            "service_end_date": {"type": "string", "format": "date"},
        },
        "required": ["member", "provider_name"],
        "additionalProperties": False,
        "x-validation-rules": [
            {
                "type": "date_order",
                "start": "/service_start_date",
                "end": "/service_end_date",
            }
        ],
    },
}


def schema_definition(
    name: str, schema: dict[str, Any], field_guide: str = "", version: str = "1"
) -> SchemaDefinition:
    # Computes a deterministic SHA-256 schema hash across canonical JSON
    # representation (sorted keys, compact separators) concatenated with the
    # raw field guide. This hash serves as the versioned provenance stamp.
    validate_schema(schema)
    if len(field_guide.encode("utf-8")) > MAX_FIELD_GUIDE_BYTES:
        raise SchemaError("The Markdown field guide exceeds 256 KB.")
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256((canonical + "\n" + field_guide).encode()).hexdigest()
    return SchemaDefinition(
        name=name.strip() or "Custom schema",
        version=version,
        schema=deepcopy(schema),
        field_guide=field_guide,
        schema_hash=digest,
    )


def template_schema(name: str) -> dict[str, Any]:
    try:
        return deepcopy(SCHEMA_TEMPLATES[name])
    except KeyError as exc:
        raise SchemaError("Choose a supported schema template.") from exc


def schema_to_field_rows(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a supported schema for the visual field editor."""
    validate_schema(schema)
    rows: list[dict[str, Any]] = []

    def visit(node: dict[str, Any], prefix: str = "") -> None:
        required = set(node.get("required", []))
        for name, child in node.get("properties", {}).items():
            path = f"{prefix}.{name}" if prefix else name
            target = child
            if child.get("type") == "array":
                path += "[]"
                target = child["items"]
            if target.get("type") == "object":
                visit(target, path)
                continue
            rows.append(
                {
                    "path": path,
                    "type": target.get("type", "string"),
                    "description": target.get("description", ""),
                    "required": name in required,
                    "format": target.get("format", ""),
                    "aliases": ", ".join(target.get("x-alternativeNames", [])),
                    "enum": ", ".join(str(value) for value in target.get("enum", [])),
                }
            )

    visit(schema)
    return rows


def compile_field_rows(rows: list[dict[str, Any]], title: str = "Custom schema") -> dict[str, Any]:
    root: dict[str, Any] = {
        "title": title.strip() or "Custom schema",
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
    seen: set[str] = set()
    for row in rows:
        path = str(row.get("path", "")).strip()
        if not path:
            continue
        if path in seen:
            raise SchemaError(f"Duplicate field path: {path}")
        seen.add(path)
        parts = path.split(".")
        if any(not _PATH_PART.fullmatch(part) for part in parts):
            raise SchemaError(f"Invalid field path: {path}")
        field_type = str(row.get("type", "string"))
        if field_type not in _PRIMITIVE_TYPES:
            raise SchemaError(f"Unsupported field type for {path}: {field_type}")
        leaf: dict[str, Any] = {"type": field_type}
        for source, target in (("description", "description"), ("pattern", "pattern")):
            value = str(row.get(source, "")).strip()
            if value:
                leaf[target] = value
        fmt = str(row.get("format", "")).strip()
        if fmt:
            leaf["format"] = fmt
        aliases = _csv_values(row.get("aliases"))
        if aliases:
            leaf["x-alternativeNames"] = aliases
        enum = _csv_values(row.get("enum"))
        if enum:
            leaf["enum"] = enum
        _insert_field(root, parts, leaf, bool(row.get("required", False)))
    validate_schema(root)
    return root


def validate_schema(schema: dict[str, Any]) -> None:
    encoded = json.dumps(schema, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_SCHEMA_BYTES:
        raise SchemaError("The schema exceeds 1 MB.")
    if schema.get("type") != "object" or not isinstance(schema.get("properties"), dict):
        raise SchemaError("The schema root must be an object with properties.")
    leaf_count = _validate_node(schema, 1)
    if leaf_count > MAX_LEAF_FIELDS:
        raise SchemaError("The schema exceeds 100 leaf fields.")


def extraction_response_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Wrap a nullable strict form of a user schema with field evidence."""
    # Adapts user schemas for OpenAI's strict Structured Outputs mode:
    # wraps the user record alongside supporting quote/page evidence, and
    # calls _strict_nullable to ensure all fields are required and nullable,
    # additionalProperties is False, and vendor extensions (x-*) are stripped.
    validate_schema(schema)
    record = _strict_nullable(deepcopy(schema))
    return {
        "type": "object",
        "properties": {
            "record": record,
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field_path": {"type": "string"},
                        "quote": {"type": "string"},
                        "page": {"type": ["integer", "null"]},
                    },
                    "required": ["field_path", "quote", "page"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["record", "evidence"],
        "additionalProperties": False,
    }


def _validate_node(node: Any, depth: int) -> int:
    if depth > MAX_SCHEMA_DEPTH:
        raise SchemaError("The schema exceeds eight nesting levels.")
    if not isinstance(node, dict):
        raise SchemaError("Every schema node must be an object.")
    unknown = set(node) - _ALLOWED_KEYS
    if unknown:
        raise SchemaError(f"Unsupported schema keyword: {sorted(unknown)[0]}")
    node_type = node.get("type")
    if node_type == "object":
        properties = node.get("properties")
        if not isinstance(properties, dict):
            raise SchemaError("Object schemas require properties.")
        required = node.get("required", [])
        if not isinstance(required, list) or not set(required) <= set(properties):
            raise SchemaError("Required fields must name properties on the same object.")
        return sum(_validate_node(child, depth + 1) for child in properties.values())
    if node_type == "array":
        return _validate_node(node.get("items"), depth + 1)
    if node_type not in _PRIMITIVE_TYPES:
        raise SchemaError(f"Unsupported schema type: {node_type}")
    return 1


def _insert_field(
    root: dict[str, Any], parts: list[str], leaf: dict[str, Any], required: bool
) -> None:
    node = root
    for index, raw_part in enumerate(parts):
        is_array = raw_part.endswith("[]")
        name = raw_part.removesuffix("[]")
        last = index == len(parts) - 1
        properties = node["properties"]
        if last:
            if name in properties:
                raise SchemaError(f"Conflicting field path: {'.'.join(parts)}")
            properties[name] = {"type": "array", "items": leaf} if is_array else leaf
            if required:
                node["required"].append(name)
            return
        expected = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        }
        child = properties.setdefault(
            name, {"type": "array", "items": expected} if is_array else expected
        )
        node = child["items"] if is_array and child.get("type") == "array" else child
        if node.get("type") != "object":
            raise SchemaError(f"Conflicting field path: {'.'.join(parts)}")


def _strict_nullable(node: dict[str, Any]) -> dict[str, Any]:
    node.pop("x-validation-rules", None)
    node.pop("x-alternativeNames", None)
    if node.get("type") == "object":
        properties = node.get("properties", {})
        node["properties"] = {name: _strict_nullable(child) for name, child in properties.items()}
        node["required"] = list(properties)
        node["additionalProperties"] = False
    elif node.get("type") == "array":
        node["items"] = _strict_nullable(node["items"])
    else:
        node["type"] = [node["type"], "null"]
        if isinstance(node.get("enum"), list) and None not in node["enum"]:
            node["enum"].append(None)
    return node


def _csv_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or "").split(",") if item.strip()]
