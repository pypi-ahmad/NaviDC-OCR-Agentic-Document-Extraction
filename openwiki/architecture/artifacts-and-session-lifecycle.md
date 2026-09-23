---
type: Architecture
title: Artifacts and Session Lifecycle
description: Explains how an extraction result is identified, held in the Streamlit session, and packaged with provenance and optional outputs.
tags: [artifacts, session-state, provenance, html, zip]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-d974d9358a2edd2a07a6386e
    resource: repo://src/agentic_document_extraction/artifacts.py
  - id: openwiki-source-964922c41d4be25ac5f159ec
    resource: repo://streamlit_app.py
  - id: openwiki-source-63fdccb791696f475b33ce12
    resource: repo://tests/test_core.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# Artifacts and Session Lifecycle

An extraction produces Markdown, an annotated PDF, a standalone HTML view, and a ZIP bundle. When structured extraction is enabled, the bundle can also include the record, schema, quality report, review audit, and uploaded field guide. NaviDC-extracted image assets are included when present. The app builds these artifacts in memory; it does not write completed results to a database.

## Result identity and session state

The Streamlit result key combines the original upload's SHA-256 digest, selected source-page range, requested layout, accuracy policy, and schema hash. The schema component is `ocr-only` when structured extraction is disabled. On a rerun, the app removes a stored result when its key no longer matches the current inputs. A human review decision updates the structured result and rebuilds the bundle before saving it back to the session.

This means session-held artifacts are temporary. Users should download the ZIP before changing inputs or ending the browser session. See [the OCR workflow](../workflows/ocr-extraction.md) and [structured extraction and review](../workflows/structured-extraction-and-review.md) for the stages that produce and update a result.

## Bundle contents and manifest

`build_bundle()` writes the Markdown, annotated PDF, HTML, and `manifest.json`. It adds structured files only when their corresponding values are supplied, and writes image assets under `images/` using each asset's base filename. The application derives user-facing artifact names from a sanitized source filename.

The manifest records the source name and type, original-byte SHA-256 digest, total page count, selected page range, generation time in UTC, OCR provider and model, layout mode, and accuracy policy. It also records the semantic model, reasoning effort, and schema hash. Optional artifact mappings appear only for outputs included in the bundle.

## HTML and display safety

The HTML view renders extracted Markdown and page markers as a standalone document. Provider HTML tables are converted to Markdown tables before rendering; other raw HTML is escaped. The page uses a restrictive Content Security Policy and does not embed the source PDF or source page images. Streamlit's rendered-Markdown view uses the same table conversion while retaining raw Markdown separately for download.

## Tests

`tests/test_core.py` checks the ZIP entry set, image inclusion, selected range and provenance fields in the manifest, Markdown table conversion, page-marker rendering, and escaping of script markup. These tests cover deterministic artifact behavior; they do not establish browser rendering fidelity for every document.

## Source paths

- [`streamlit_app.py`](../../streamlit_app.py) owns the result key, session invalidation, review update, and bundle handoff.
- [`artifacts.py`](../../src/agentic_document_extraction/artifacts.py) builds artifact names, manifests, ZIP files, and HTML.
- [`test_core.py`](../../tests/test_core.py) checks bundle composition and safe display conversion.
- [Configuration and artifact reference](../../docs/configuration-and-artifacts.md) lists the user-facing filenames and optional bundle entries.
