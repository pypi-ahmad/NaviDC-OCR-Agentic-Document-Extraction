---
type: Workflow
title: Document Ingestion and Scan Quality
description: Follows uploads through validation, normalization, inclusive page selection, scan assessment, optional enhancement, and automatic layout choice.
tags: [documents, ingestion, scan-quality, page-selection, layout]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-b14f40478276203031f0897c
    resource: repo://src/agentic_document_extraction/documents.py
  - id: openwiki-source-3dc64ccb9d9887e0b123ebd5
    resource: repo://src/agentic_document_extraction/quality.py
  - id: openwiki-source-78f2911082259f99ffe15453
    resource: repo://tests/test_agentic.py
  - id: openwiki-source-63fdccb791696f475b33ce12
    resource: repo://tests/test_core.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# Document Ingestion and Scan Quality

The ingestion boundary turns a supported upload into validated metadata and PDF bytes before OCR. The quality stage then selects the requested source pages, rasterizes them, records scan signals, and prepares the pixels sent to the worker. It does not perform layout detection or OCR; NaviDC owns those steps.

## Validate and normalize the upload

`inspect_document()` rejects empty files, uploads larger than 100 MB, unsupported extensions, and damaged or unreadable content. PyMuPDF checks PDFs, rejects password-protected or zero-page documents, and retains valid PDF bytes. Pillow opens supported PNG, JPG/JPEG, and TIF/TIFF images; images are EXIF-corrected, flattened against white, and converted to a one-page PDF. Only the first TIFF frame is used.

The original upload's SHA-256 digest and source metadata travel with the normalized PDF. The source filename is reduced to a bounded safe stem for artifact names.

## Select source pages

Page ranges at the UI boundary are one-based and inclusive. `select_pdf_pages()` validates the range, translates it to PyMuPDF's zero-based indices, and copies those pages into a new PDF in source order. The app also carries the original page numbers alongside the selected PDF so OCR markers and evidence can refer back to source pages.

## Assess and prepare scan quality

`prepare_document()` renders selected pages at 400 DPI for `Maximum` and 300 DPI for `Fast` or `Balanced`. It assesses blur, contrast, skew, uneven illumination, compression, and clipped-edge risk. These signals and their thresholds are heuristics tuned to the checked machine and scan conditions; they are not calibrated accuracy scores or universal cutoffs.

`Fast` skips enhancement. `Balanced` and `Maximum` apply only the corrections indicated by the page warnings, in a fixed order: illumination normalization, contrast enhancement, light denoising, mild sharpening, then deskew. The generated `QualityReport` records the effective DPI, per-page signals, warnings, and transformations.

## Choose the layout mode

For `Auto`, `recommend_layout()` selects `Segmentation` when more than half of the selected pages show skew, uneven illumination, or clipped-edge risk. Otherwise it selects `Detection`. This is a local heuristic for choosing NaviDC's layout strategy, not a learned guarantee that one mode will produce better OCR for every document.

The next step is the [local OCR extraction workflow](ocr-extraction.md). The [validation map](../testing/validation-and-tests.md) lists the focused tests for page ordering and one low-contrast enhancement case.

## Source paths

- [`documents.py`](../../src/agentic_document_extraction/documents.py) owns upload checks, image normalization, safe names, and source-page selection.
- [`quality.py`](../../src/agentic_document_extraction/quality.py) owns rendering, warning signals, enhancements, and Auto layout selection.
- [`models.py`](../../src/agentic_document_extraction/models.py) defines the immutable document and quality result objects.
- [`test_core.py`](../../tests/test_core.py) checks inclusive page ranges and selected-page order.
- [`test_agentic.py`](../../tests/test_agentic.py) checks a low-contrast warning and enhancement.
