---
type: Operations
title: Local Runtime, Configuration, and Security
description: Covers the Windows Streamlit launcher, isolated WSL OCR worker, default ports and runtime settings, capacity limits, and supported trust model.
tags: [operations, windows, wsl, configuration, security]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-23T14:56:11.943Z
sources:
  - id: openwiki-source-ea1410db2f32ca9e03aefece
    resource: repo://.streamlit/config.toml
  - id: openwiki-source-e7faa3ddaca50993ae19c88a
    resource: repo://launch.cmd
  - id: openwiki-source-3a44815832a872f4778f822b
    resource: repo://SECURITY.md
  - id: openwiki-source-b0d1169449685d22b9cb6fa2
    resource: repo://src/agentic_document_extraction/provider.py
  - id: openwiki-source-54b83b5c29cb3b1919d9b407
    resource: repo://src/agentic_document_extraction/semantic.py
  - id: openwiki-source-353f1d6ea1c644afb69c0f2f
    resource: repo://src/agentic_document_extraction/worker.py
generated: { by: "codex", at: "2026-09-23T14:56:11.943Z" }
---

# Local Runtime, Configuration, and Security

## Runtime layout

The Streamlit app runs from the repository's `uv` environment on port `8741`. The NaviDC FastAPI worker starts on the first extraction and listens on `127.0.0.1:8742` inside the configured WSL distribution. The worker uses the separate NaviDC Python 3.12 environment; the app environment does not contain the NaviDC, PyTorch, CUDA, or vLLM runtime.

On Windows, `launch.cmd` starts Streamlit with `uv run` and passes through additional command-line arguments. Before startup it stops the matching Streamlit app and terminates listeners on port `8741`. If that port may be used by another service, inspect the listener before running the launcher. When a healthy OCR worker is already present, the launcher stops it so the next worker's logs attach to the launcher console.

The worker is configured for `StarDoc-AI/NaviDC-OCR`, the `vllm-async-engine` backend, `MAX_MODEL_LEN=8192`, `GPU_MEMORY_UTILIZATION=0.85`, and one PDF worker. An async lock serializes extraction requests. These settings reflect the checked local GPU configuration; they are not general capacity guarantees.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `NAVIDC_RUNTIME_DIR` | `/home/ahmad/projects/NaviDC-OCR` | NaviDC runtime directory inside WSL |
| `NAVIDC_PROVIDER_URL` | `http://127.0.0.1:8742` | Worker URL used by the app |
| `NAVIDC_PROVIDER_PORT` | `8742` | Port used when the adapter starts the worker |

Keep `NAVIDC_PROVIDER_URL` and `NAVIDC_PROVIDER_PORT` consistent when changing the port. The Streamlit configuration sets port `8741`, headless mode, and a 100 MB upload limit. Optional structured extraction also requires user-scoped `OPENAI_API_KEY` and `OPENAI_BASE_URL`; do not put their values in this repository.

## Health and troubleshooting

The Streamlit health endpoint is `http://127.0.0.1:8741/_stcore/health`; the worker exposes `http://127.0.0.1:8742/health`. Before the first extraction, the worker may not exist, so a connection failure on port `8742` is expected. A ready health response means the API process is available; it does not mean NaviDC has finished loading the model into GPU memory.

If the worker fails to start, check the configured WSL distribution, runtime interpreter, and GPU visibility. If it exits during inference, check GPU memory and reduce the selected page range. See the [operations runbook](../../docs/operations-runbook.md) for exact diagnostics and recovery commands, and the [provider contract](../architecture/provider-worker-contract.md) for request limits and error mapping.

## Security boundary

This project is designed for one trusted local user and is not hardened for public internet or hostile multi-tenant use. The worker binds to loopback. Do not expose ports `8741` or `8742` to an untrusted network without authentication, authorization, request limits, TLS termination, and appropriate isolation. Uploaded documents remain untrusted input even during local use. The [security guidance](../../SECURITY.md) describes protected data and controls that are not implemented.

## Source paths

- [`launch.cmd`](../../launch.cmd) manages the local Streamlit startup and worker log lifecycle.
- [`.streamlit/config.toml`](../../.streamlit/config.toml) defines the app port, upload limit, and display settings.
- [`provider.py`](../../src/agentic_document_extraction/provider.py) resolves runtime variables and starts the worker.
- [`worker.py`](../../src/agentic_document_extraction/worker.py) sets the NaviDC runtime configuration and serializes GPU work.
- [Security guidance](../../SECURITY.md) sets the supported deployment boundary.
