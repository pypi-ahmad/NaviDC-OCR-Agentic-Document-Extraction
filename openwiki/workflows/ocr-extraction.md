---
type: Workflow
title: Local OCR Extraction Workflow
description: Traces a user request from upload and page preparation through the local NaviDC worker and into downloadable artifacts, with the optional semantic branch called out.
tags: [ocr, extraction, workflow, streamlit, navidc]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-b0d1169449685d22b9cb6fa2
    resource: repo://src/agentic_document_extraction/provider.py
  - id: openwiki-source-54b83b5c29cb3b1919d9b407
    resource: repo://src/agentic_document_extraction/semantic.py
  - id: openwiki-source-353f1d6ea1c644afb69c0f2f
    resource: repo://src/agentic_document_extraction/worker.py
  - id: openwiki-source-964922c41d4be25ac5f159ec
    resource: repo://streamlit_app.py
  - id: openwiki-source-78f2911082259f99ffe15453
    resource: repo://tests/test_agentic.py
  - id: openwiki-source-63fdccb791696f475b33ce12
    resource: repo://tests/test_core.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# Local OCR Extraction Workflow

The default path produces OCR artifacts without structured extraction. Streamlit validates the uploaded file before presenting the source preview. When the user starts extraction, it selects source pages, prepares their scan quality, calls the local provider, and builds the results in the UI process.

## Main OCR path

1. `inspect_document()` validates the upload and returns metadata, its original-byte digest, and PDF bytes. Raster images are normalized before this point returns.
2. `process_document()` copies the requested one-based inclusive page range into a new PDF and prepares it at the DPI selected by the accuracy policy.
3. For `Auto`, the app chooses `Detection` or `Segmentation` from the page-quality report. It then calls `NaviDcProvider.ensure_running()` and sends the prepared PDF, source-page mapping, layout mode, and DPI to `/extract`.
4. The WSL worker validates the request and waits for the extraction lock. It calls NaviDC's async parser, maps output pages back to original page numbers, and returns Markdown, middle JSON, an annotated PDF, and any extracted images in a ZIP.
5. The provider checks the required ZIP entries and returns a normalized `ProviderOutput`. The Streamlit process creates standalone HTML and a final user-facing bundle, then stores the result in session state.

The worker handles one extraction at a time. A later request waits for the active job rather than competing for the configured GPU allocation. See the [provider-worker contract](../architecture/provider-worker-contract.md) for request validation, startup, and failure details.

## Optional structured branch

When the user confirms a schema, the app passes OCR Markdown and the worker's layout representation to the structured-extraction workflow. That workflow asks the semantic provider for field values and evidence, resolves quotes against OCR blocks, validates the record, and may make up to two correction calls. Unverified values are not silently accepted; fields without supporting blocks are nulled and the result can require manual review.

If `Maximum` accuracy is selected and structured validation or grounding still requires review, the app runs OCR once more using the alternate layout mode. It keeps the alternate result only if its field-and-issue objective strictly improves. If the semantic endpoint fails, the UI can still return the completed OCR artifacts and reports the structured-extraction error separately.

Details are in [structured extraction, grounding, and review](structured-extraction-and-review.md). The result key and artifact lifecycle are described in [Artifacts and Session Lifecycle](../architecture/artifacts-and-session-lifecycle.md).

## Failure boundaries

Upload and page-range errors are rejected before OCR. Worker startup, transport, timeout, invalid archive, and NaviDC failures become bounded provider errors. The app does not fabricate OCR output when the worker fails. An optional semantic failure does not erase a completed OCR result.

## Verification limits

The repository's unit tests cover deterministic page selection, artifact handling, quality signals, and fake-provider semantic behavior. They do not launch the worker or perform GPU inference. A provider change therefore needs the documented live extraction check in addition to unit tests; see [Validation and Test Coverage](../testing/validation-and-tests.md).

## Source paths

- [`streamlit_app.py`](../../streamlit_app.py) coordinates the flow and optional alternate-layout pass.
- [`documents.py`](../../src/agentic_document_extraction/documents.py) validates uploads and selects pages.
- [`quality.py`](../../src/agentic_document_extraction/quality.py) prepares pages and recommends Auto layout.
- [`provider.py`](../../src/agentic_document_extraction/provider.py) starts the local worker and validates its response.
- [`worker.py`](../../src/agentic_document_extraction/worker.py) runs NaviDC and packages provider output.
- [`test_core.py`](../../tests/test_core.py) verifies deterministic page-selection and artifact behaviors.
