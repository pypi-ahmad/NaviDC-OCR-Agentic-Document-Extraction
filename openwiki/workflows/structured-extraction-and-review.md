---
type: Workflow
title: Structured Extraction, Grounding, and Review
description: Explains how confirmed schemas are sent with OCR text, how returned fields are grounded and validated, and how bounded correction and human review update the result.
tags: [structured-extraction, schemas, grounding, validation, review]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-4fc5023e5022a5209c90b9a9
    resource: repo://src/agentic_document_extraction/grounding.py
  - id: openwiki-source-579ce298c94f83641b305e11
    resource: repo://src/agentic_document_extraction/models.py
  - id: openwiki-source-c48776254467686a629735bb
    resource: repo://src/agentic_document_extraction/schemas.py
  - id: openwiki-source-54b83b5c29cb3b1919d9b407
    resource: repo://src/agentic_document_extraction/semantic.py
  - id: openwiki-source-7620a61b0f8993c36a02c169
    resource: repo://src/agentic_document_extraction/validation.py
  - id: openwiki-source-78f2911082259f99ffe15453
    resource: repo://tests/test_agentic.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# Structured Extraction, Grounding, and Review

Structured extraction is an optional stage after local OCR. It maps OCR Markdown to a confirmed schema, requires supporting evidence for non-null leaf values, runs deterministic checks, and exposes unresolved fields for human review. It does not replace the local OCR worker.

## Define and confirm a schema

The UI offers built-in templates, a visual field builder, and an advanced JSON Schema editor. An optional trusted Markdown field guide can be used to draft a schema through the semantic provider. The user must confirm the schema before it is used for extraction.

`schemas.py` compiles field rows into nested objects and arrays, rejects unsupported schema keywords, and enforces bounds on schema size, nesting, field count, and guide size. A canonical hash covers the schema and field guide; the app includes that hash in the extraction result key and bundle metadata.

## Request and evidence contract

`OpenAISemanticProvider` requires `OPENAI_API_KEY` and `OPENAI_BASE_URL` and checks that the configured endpoint exposes `gpt-5.6-luna`. The structured request contains the confirmed schema, optional field guide, OCR Markdown, and any correction context. The prompt treats document text as untrusted data and asks for an exact supporting quote and source-page number for each non-null leaf. Source PDF and image bytes are not included in this semantic request.

The response is requested in strict JSON Schema form. `grounding.py` reads layout blocks from NaviDC's `middle_json`, maps them to original source pages, and resolves each model-provided quote to a block. A fuzzy match must score at least `0.90` to bind a quote to a block. If no block supports a non-null value, it is treated as ungrounded.

## Validation and bounded correction

`validation.py` applies JSON Schema validation and the supported cross-field rules: item totals, field totals, date order, and equality. It builds per-field results from schema issues and evidence matches; its weighted confidence and status labels are local review signals, not calibrated probabilities.

`run_structured_extraction()` makes an initial model call and allows up to two correction calls by default. Each correction receives the previous result and issues. The workflow keeps a candidate only when the lexicographic objective improves: valid fields first, grounded fields next, then fewer issues. Before returning, it replaces non-null values without a supporting OCR block with `null` and recalculates validation. Any remaining issue or field not marked `verified` sets `review_required`.

## Human review

Automated statuses (`verified`, `review`, `blocked`) are distinct from human decisions (`accepted`, `corrected`, `rejected`). In the Review tab, a user can accept, correct, or reject a field. `apply_manual_review()` records a timestamped event with the field path and old/new values. A changed value loses its prior evidence binding and receives a lower review score; the record is validated again and the bundle is rebuilt.

The app also has a narrow retry path: when `Maximum` accuracy is selected and structured extraction still requires review, it runs OCR with the alternate layout mode and keeps that result only if the objective improves. See the [main OCR workflow](ocr-extraction.md).

## Tests and limits

Tests cover nested schema compilation, unsupported-key rejection, strict nullable adaptation, exact quote grounding, schema and total validation, an improved grounded correction, bounded retries that null an unsupported value, and low-contrast image enhancement. These tests do not measure endpoint accuracy or establish model behavior on a document corpus. See [Validation and Test Coverage](../testing/validation-and-tests.md).

## Source paths

- [`schemas.py`](../../src/agentic_document_extraction/schemas.py) compiles and constrains schemas.
- [`semantic.py`](../../src/agentic_document_extraction/semantic.py) makes model requests, manages corrections, and records manual review events.
- [`grounding.py`](../../src/agentic_document_extraction/grounding.py) maps quotes to OCR blocks.
- [`validation.py`](../../src/agentic_document_extraction/validation.py) checks schemas, cross-field rules, and field status.
- [`models.py`](../../src/agentic_document_extraction/models.py) separates automated field status from human review action.
- [`test_agentic.py`](../../tests/test_agentic.py) exercises the deterministic structured-extraction behaviors.
