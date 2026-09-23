---
type: Architecture
title: Provider and Worker Contract
description: Traces the local OCR adapter from worker startup and HTTP requests through serialized NaviDC inference and archive validation.
tags: [provider, worker, api, wsl, ocr]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-b0d1169449685d22b9cb6fa2
    resource: repo://src/agentic_document_extraction/provider.py
  - id: openwiki-source-353f1d6ea1c644afb69c0f2f
    resource: repo://src/agentic_document_extraction/worker.py
  - id: openwiki-source-78f2911082259f99ffe15453
    resource: repo://tests/test_agentic.py
  - id: openwiki-source-63fdccb791696f475b33ce12
    resource: repo://tests/test_core.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# Provider and Worker Contract

The Streamlit application depends on the `OcrProvider` protocol and normalized `ProviderOutput`, not on NaviDC internals. `NaviDcProvider` implements that boundary over a loopback HTTP API. The FastAPI worker is the only application module that imports NaviOCR and vLLM; it runs in the separate WSL runtime.

## Client lifecycle

`health()` performs a short request and folds transport or invalid-JSON failures into an `unavailable` result. Before extraction, `ensure_running()` reuses a ready worker or starts one and polls until it is ready, the process exits, or the startup window expires. This check reports worker readiness, not whether the model has already loaded into GPU memory.

The extraction request sends the selected PDF, original one-based page numbers, layout mode, and render DPI as multipart form data. The client allows up to 1,800 seconds for extraction with a 10-second connection timeout. It converts timeout, transport, and malformed-result failures into bounded provider errors rather than exposing raw exceptions. On Windows, startup translates the repository source path with `wslpath` before placing it on the worker's `PYTHONPATH`.

## Worker request path

Before importing NaviOCR's engine, the worker applies the fixed model, backend, token-length, GPU-memory, and PDF-worker settings. It binds the FastAPI service to loopback when launched by the provider. `/health` reports the configured provider, model, and maximum render DPI.

`POST /extract` accepts only `Detection` or `Segmentation`, the supported render DPIs, a non-empty JSON list of positive integer source-page numbers, and a non-empty PDF no larger than 100 MB. Invalid request values receive `422`; NaviDC failures receive a generic `500` message. An `asyncio.Lock` serializes extraction because the configured GPU allocation is intended for one job at a time.

NaviDC's parser does not accept the requested render DPI through this integration API. `_run_extraction()` temporarily wraps its PDF rasterizer to pass the selected DPI, then restores the original function in a `finally` block. The lock protects this module-level patch from concurrent requests. Each request uses a temporary directory, which is removed when processing ends.

## ZIP contract

The worker returns an in-memory ZIP with `result.md`, `annotated.pdf`, and `middle.json`, plus an optional `images/` directory. Markdown page markers carry the original source page numbers so later stages can retain page provenance. The provider adapter rejects archives missing any required entry and converts a valid archive into `ProviderOutput`.

## Verification boundary

The current tests exercise page-selection, schema/grounding behavior, and artifact packaging. Structured-extraction tests use a fake provider; they do not start WSL, contact the FastAPI worker, or run NaviDC on a GPU. The [validation map](../testing/validation-and-tests.md) separates those deterministic checks from the documented live extraction check.

## Source paths

- [`provider.py`](../../src/agentic_document_extraction/provider.py) defines the adapter protocol, worker lifecycle, HTTP client, error mapping, and ZIP parsing.
- [`worker.py`](../../src/agentic_document_extraction/worker.py) defines the API checks, NaviDC configuration, serialized execution, temporary files, and response archive.
- [`provider-api.md`](../../docs/provider-api.md) documents the HTTP request and response contract.
- [`test_agentic.py`](../../tests/test_agentic.py) uses a fake provider for semantic workflow tests.
