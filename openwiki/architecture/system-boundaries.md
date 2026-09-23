---
type: Architecture
title: System Boundaries and Component Ownership
description: Maps the local Streamlit app, isolated NaviDC worker, optional semantic provider, and the boundaries between document data and model services.
tags: [architecture, boundaries, streamlit, wsl, security]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-3a44815832a872f4778f822b
    resource: repo://SECURITY.md
  - id: openwiki-source-b14f40478276203031f0897c
    resource: repo://src/agentic_document_extraction/documents.py
  - id: openwiki-source-b0d1169449685d22b9cb6fa2
    resource: repo://src/agentic_document_extraction/provider.py
  - id: openwiki-source-54b83b5c29cb3b1919d9b407
    resource: repo://src/agentic_document_extraction/semantic.py
  - id: openwiki-source-353f1d6ea1c644afb69c0f2f
    resource: repo://src/agentic_document_extraction/worker.py
  - id: openwiki-source-964922c41d4be25ac5f159ec
    resource: repo://streamlit_app.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# System Boundaries and Component Ownership

The application has two independent processing paths. OCR runs locally through a Streamlit UI, an HTTP adapter, and a FastAPI worker in WSL that imports NaviDC-OCR and vLLM. Optional structured extraction runs after OCR through an environment-configured OpenAI-compatible endpoint. Artifact assembly and session state remain in the Streamlit process.

## Component ownership

- **Streamlit app:** accepts uploads, owns page and accuracy controls, coordinates extraction, presents review, and provides downloads. It calls the typed provider boundary instead of importing the OCR engine.
- **Document and quality modules:** validate and normalize uploads, select pages, render and assess scans, and prepare the PDF that goes to OCR.
- **Provider adapter:** starts or reuses the local worker, sends selected pages over HTTP, and normalizes the returned ZIP into `ProviderOutput`.
- **WSL worker:** applies NaviDC's fixed runtime configuration, serializes GPU requests, invokes `aio_do_parse`, and returns provider artifacts. It is the only application module importing NaviOCR.
- **Semantic extraction modules:** when enabled, send OCR Markdown, the confirmed schema, an optional field guide, and any bounded correction context to the configured endpoint. They ground returned fields against OCR layout evidence and apply deterministic validation locally.
- **Artifact builder:** creates the standalone HTML view, provenance manifest, and final ZIP in the Streamlit process.

The OCR boundary and its request/response lifecycle are detailed in [the provider-worker contract](provider-worker-contract.md). The end-to-end sequence is in [the OCR workflow](../workflows/ocr-extraction.md); structured extraction is covered in [its own workflow page](../workflows/structured-extraction-and-review.md).

## Data and trust boundaries

Uploaded PDFs and images are treated as untrusted. The document layer enforces supported formats, size and readability checks, rejects password-protected PDFs, and normalizes images before later stages. Only the selected PDF pages are sent to the local OCR worker.

Structured extraction is optional. Its request is built from extracted Markdown, the confirmed schema, and the optional field guide; source PDF/image bytes are not sent to that endpoint by this code path. The semantic provider requires user-scoped `OPENAI_API_KEY` and `OPENAI_BASE_URL` settings. The model is instructed to treat document text as data, and returned field values must be matched to OCR evidence and validated before the app presents them for review.

This is a trusted, single-user local application, not a hardened public or multi-tenant service. The worker is launched on loopback; network exposure and document retention remain operational security boundaries. See [local runtime and security](../operations/local-runtime.md).

## Runtime separation

The Streamlit environment is managed from the repository with `uv`. NaviDC-OCR, PyTorch, CUDA, and vLLM live in the separate WSL runtime. The adapter translates the repository source path for WSL and reaches the worker through its loopback API. This keeps the UI dependency environment separate from the validated GPU stack.

The design decision and its trade-offs are recorded in [ADR-001](../../docs/adr/001-isolated-ocr-worker.md). Runtime and launch details are in [the operations page](../operations/local-runtime.md).

## Source paths

- [`streamlit_app.py`](../../streamlit_app.py) coordinates user inputs, OCR, optional semantic extraction, review, and downloads.
- [`provider.py`](../../src/agentic_document_extraction/provider.py) owns the application-facing OCR adapter.
- [`worker.py`](../../src/agentic_document_extraction/worker.py) owns the NaviDC import and inference boundary.
- [`semantic.py`](../../src/agentic_document_extraction/semantic.py) owns the optional external model request and correction workflow.
- [Security guidance](../../SECURITY.md) defines the intended deployment and trust limits.
