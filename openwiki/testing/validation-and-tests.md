---
type: Testing
title: Validation and Test Coverage
description: Maps automated tests and configured quality gates to the behaviors they check, and identifies the live OCR integration check that remains separate.
tags: [testing, validation, pytest, ruff, typing]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-83e9451fd99a1038793b8456
    resource: repo://docs/developer-guide.md
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-78f2911082259f99ffe15453
    resource: repo://tests/test_agentic.py
  - id: openwiki-source-63fdccb791696f475b33ce12
    resource: repo://tests/test_core.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# Validation and Test Coverage

The test suite covers deterministic document, artifact, scan-quality, schema, grounding, validation, correction, and review behavior. It does not start the WSL worker or run NaviDC inference on a GPU. Keep that distinction when reporting verification: unit tests do not establish a successful live extraction.

## What the tests cover

| Area | Verified behavior |
|---|---|
| Page selection | Inclusive page-range acceptance/rejection and source-order preservation in the selected PDF |
| Bundle and display | ZIP contents and manifest values, Markdown table conversion, source-page markers, no embedded source PDF, and escaping of unsafe HTML |
| Schema handling | Nested field compilation, rejection of unsupported keywords, and strict nullable response-schema generation |
| Evidence and validation | Exact quote-to-page/bounding-box resolution, schema format checks, and cross-field total rules |
| Correction and review | A grounded correction can improve a result; values without supporting evidence are nulled after bounded attempts and require review |
| Scan quality | A low-contrast sample produces a warning and the configured contrast enhancement |

`test_agentic.py` uses a fake semantic provider for correction behavior. Neither test module exercises a live OpenAI-compatible endpoint or HTTP provider worker.

## Project quality gates

The project documents these application checks:

```powershell
uv run pytest
uv run ruff format --check src tests streamlit_app.py
uv run ruff check src tests streamlit_app.py
uv run ty check src
```

The `ty` configuration excludes `worker.py` because NaviOCR and FastAPI are installed only in the separate WSL runtime. The developer guide also provides a `py_compile` command using that runtime's Python interpreter. For provider changes, the documented integration check is one real extraction with `input/navidc-smoke-test.pdf`, followed by inspection of Markdown, the annotated PDF, HTML, and the ZIP manifest.

## Reading test results

The tests use synthetic PDFs, generated image arrays, fixture middle JSON, and fake model responses. They establish the asserted branch behavior, not OCR accuracy across a document corpus, GPU capacity, browser rendering, or current endpoint availability. See [the provider-worker contract](../architecture/provider-worker-contract.md) for the boundary the live check must cross and [document ingestion and quality](../workflows/document-ingestion-and-quality.md) for the tested scan-quality behavior.

## Source paths

- [`test_core.py`](../../tests/test_core.py) checks page selection, bundle composition, manifest fields, and safe Markdown/HTML rendering.
- [`test_agentic.py`](../../tests/test_agentic.py) checks schema, grounding, validation, correction, and scan-quality behavior.
- [`pyproject.toml`](../../pyproject.toml) configures pytest, Ruff, and the `ty` worker exclusion.
- [Developer guide](../../docs/developer-guide.md) records the quality gates and worker/live extraction checks.
