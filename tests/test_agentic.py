from __future__ import annotations

from typing import Any

import cv2
import numpy as np
import pytest

from agentic_document_extraction.grounding import build_evidence_blocks, resolve_evidence
from agentic_document_extraction.quality import analyze_page, enhance_page
from agentic_document_extraction.schemas import (
    SchemaError,
    compile_field_rows,
    extraction_response_schema,
    schema_definition,
)
from agentic_document_extraction.semantic import run_structured_extraction
from agentic_document_extraction.validation import validate_record


def test_field_builder_compiles_nested_array_schema() -> None:
    schema = compile_field_rows(
        [
            {
                "path": "invoice_number",
                "type": "string",
                "required": True,
                "aliases": "invoice, invoice no",
            },
            {
                "path": "items[].amount",
                "type": "number",
                "required": True,
                "description": "Line amount",
            },
        ],
        "Invoice",
    )

    assert schema["required"] == ["invoice_number"]
    assert schema["properties"]["items"]["items"]["properties"]["amount"]["type"] == "number"
    assert schema["properties"]["invoice_number"]["x-alternativeNames"] == [
        "invoice",
        "invoice no",
    ]


def test_schema_rejects_unsupported_keywords() -> None:
    with pytest.raises(SchemaError, match="Unsupported schema keyword"):
        schema_definition(
            "Unsafe",
            {"type": "object", "properties": {}, "required": [], "oneOf": []},
        )


def test_extraction_response_makes_missing_leaf_nullable_and_strict() -> None:
    schema = {
        "type": "object",
        "properties": {"status": {"type": "string", "enum": ["open", "closed"]}},
        "required": ["status"],
        "additionalProperties": False,
    }

    wrapped = extraction_response_schema(schema)
    status = wrapped["properties"]["record"]["properties"]["status"]

    assert status["type"] == ["string", "null"]
    assert status["enum"] == ["open", "closed", None]
    assert wrapped["additionalProperties"] is False


def test_grounding_resolves_exact_quote_to_page_and_bbox() -> None:
    blocks = build_evidence_blocks(_middle_json(), [2])

    evidence = resolve_evidence("/total", "Total: USD 123.45", 2, blocks)

    assert evidence.block_id == "p2-b1"
    assert evidence.page == 2
    assert evidence.bbox == (70.0, 116.0, 163.0, 129.0)
    assert evidence.match_score == 1.0


def test_validation_checks_required_format_and_total_rule() -> None:
    schema = {
        "type": "object",
        "properties": {
            "date": {"type": "string", "format": "date"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"amount": {"type": "number"}},
                    "required": ["amount"],
                    "additionalProperties": False,
                },
            },
            "total": {"type": "number"},
        },
        "required": ["date", "total"],
        "additionalProperties": False,
        "x-validation-rules": [
            {
                "type": "sum_items_equals",
                "target": "/total",
                "items": "/items",
                "value": "/amount",
            }
        ],
    }

    issues = validate_record(
        {"date": "06/12/2024", "items": [{"amount": 10}, {"amount": 5}], "total": 16},
        schema,
    )

    assert {issue.code for issue in issues} == {"schema.format", "rule.total"}


def test_agentic_retry_accepts_grounded_improvement() -> None:
    schema = schema_definition(
        "Invoice",
        {
            "type": "object",
            "properties": {"total": {"type": "number"}},
            "required": ["total"],
            "additionalProperties": False,
        },
    )
    provider = _FakeProvider(
        [
            {
                "record": {"total": 123.45},
                "evidence": [{"field_path": "/total", "quote": "wrong", "page": 2}],
            },
            {
                "record": {"total": 123.45},
                "evidence": [{"field_path": "/total", "quote": "Total: USD 123.45", "page": 2}],
            },
        ]
    )

    result = run_structured_extraction(
        provider,
        "<!-- Page 2 -->\nTotal: USD 123.45",
        _middle_json(),
        [2],
        schema,
    )

    assert result.attempts == 2
    assert result.fields[0].status == "verified"
    assert result.review_required is False
    assert provider.corrections[1]


def test_agentic_extraction_nulls_unsupported_value_after_bounded_retries() -> None:
    schema = schema_definition(
        "Invoice",
        {
            "type": "object",
            "properties": {"total": {"type": "number"}},
            "required": ["total"],
            "additionalProperties": False,
        },
    )
    payload = {
        "record": {"total": 999.0},
        "evidence": [{"field_path": "/total", "quote": "not present", "page": 2}],
    }
    provider = _FakeProvider([payload, payload, payload])

    result = run_structured_extraction(
        provider, "<!-- Page 2 -->\nTotal: USD 123.45", _middle_json(), [2], schema
    )

    assert result.record["total"] is None
    assert result.review_required is True
    assert result.attempts == 3


def test_quality_analysis_flags_and_improves_low_contrast_page() -> None:
    image = np.full((500, 800, 3), 220, dtype=np.uint8)
    cv2.putText(image, "Low contrast", (80, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (190, 190, 190), 3)

    report = analyze_page(image, 1, 300)
    enhanced, transforms = enhance_page(image, report)

    assert "low_contrast" in report.warnings
    assert "contrast_enhancement" in transforms
    assert enhanced.shape == image.shape


class _FakeProvider:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self.payloads = iter(payloads)
        self.corrections: list[str] = []

    def generate_schema(self, field_guide: str, name: str) -> dict[str, Any]:
        raise AssertionError("not used")

    def extract(
        self, markdown: str, definition: Any, correction_context: str = ""
    ) -> dict[str, Any]:
        self.corrections.append(correction_context)
        return next(self.payloads)


def _middle_json() -> dict[str, Any]:
    return {
        "pdf_info": [
            {
                "para_blocks": [
                    {
                        "bbox": [70, 80, 188, 94],
                        "type": "text",
                        "lines": [{"spans": [{"content": "Invoice: INV-2026-0829"}]}],
                    },
                    {
                        "bbox": [70, 116, 163, 129],
                        "type": "text",
                        "lines": [{"spans": [{"content": "Total: USD 123.45"}]}],
                    },
                ]
            }
        ]
    }
