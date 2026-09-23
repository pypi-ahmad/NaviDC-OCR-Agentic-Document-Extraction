---
type: Guide
title: Quickstart and Documentation Map
description: Shows the local setup and first OCR run, then routes developers to the architecture, workflows, runtime, and test pages.
tags: [quickstart, setup, local-ocr, navigation]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-efb9b3d4a2117db869bdef1d
    resource: repo://docs/tutorial-first-extraction.md
  - id: openwiki-source-e7faa3ddaca50993ae19c88a
    resource: repo://launch.cmd
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
  - id: openwiki-source-964922c41d4be25ac5f159ec
    resource: repo://streamlit_app.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# Quickstart and Documentation Map

This repository contains a local Streamlit document-extraction app and a separate NaviDC-OCR worker in WSL. Set up the app environment separately from the GPU runtime; the app does not install NaviDC, PyTorch, CUDA, or vLLM into its `.venv`.

## Prerequisites

- Windows 11 with WSL 2 and the `Ubuntu-24.04` distribution
- An NVIDIA GPU available inside WSL
- `uv` available in PowerShell
- The NaviDC runtime at `/home/ahmad/projects/NaviDC-OCR`

## Run the first extraction

From PowerShell at the repository root:

```powershell
uv sync --all-groups
.\launch.cmd
```

Open <http://localhost:8741>. Upload a supported PDF or image, choose the PDF page range if needed, and select **Extract document**. The OCR worker starts when the first extraction begins; initial model loading can take several minutes. The default route returns OCR artifacts. Structured extraction is optional and requires a confirmed schema and configured endpoint credentials.

Download the ZIP bundle before changing the file, selected pages, layout, accuracy policy, or schema. Results are held in the Streamlit session rather than stored in an application database.

## Where to go next

- [System boundaries](architecture/system-boundaries.md) explains the app, WSL worker, and optional semantic service.
- [Document ingestion and scan quality](workflows/document-ingestion-and-quality.md) covers supported inputs, page selection, and preparation.
- [Local OCR extraction](workflows/ocr-extraction.md) traces the main request path.
- [Structured extraction and review](workflows/structured-extraction-and-review.md) covers schemas, grounding, validation, and human decisions.
- [Local runtime and security](operations/local-runtime.md) covers ports, configuration, startup, and deployment boundaries.
- [Validation and tests](testing/validation-and-tests.md) maps unit tests to behavior and describes the live provider check.

## Source paths

- [`README.md`](../README.md) is the project overview and current quick-start reference.
- [`launch.cmd`](../launch.cmd) starts the Streamlit app on port `8741`.
- [`streamlit_app.py`](../streamlit_app.py) owns the user workflow.
- [`pyproject.toml`](../pyproject.toml) declares application dependencies and quality tools.
- [First-extraction tutorial](../docs/tutorial-first-extraction.md) provides a guided sample run.
