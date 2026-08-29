# ADR-001: Isolate NaviDC-OCR behind a local worker

- Status: Accepted
- Date: 2026-08-29

## Context

NaviDC-OCR depends on a GPU-focused Python 3.12 stack containing PyTorch, CUDA support, vLLM, Transformers, and the NaviDC package. The user interface depends on current Streamlit, PyMuPDF, Pillow, and HTTPX packages.

Installing both stacks into one environment would increase dependency conflicts, environment size, startup coupling, and the risk that UI upgrades break the validated OCR runtime. NaviDC's optional upstream dependency sets also have constraints that are not needed by this application.

The machine already has a working NaviDC runtime in WSL and a public model downloaded locally.

## Decision

Run Streamlit in the repository's `uv` environment and run NaviDC-OCR in a separate FastAPI worker using `/home/ahmad/projects/NaviDC-OCR/.venv`.

The processes communicate over a loopback-only multipart HTTP API:

- Streamlit listens on port 8741.
- The worker listens on port 8742.
- The worker starts lazily and remains available for model reuse.
- The worker serializes GPU extraction requests.
- The request contains only the selected PDF pages and source-page mapping.
- The response is a ZIP containing the provider artifacts.

## Consequences

### Positive

- UI dependencies remain small and independently upgradeable.
- The validated NaviDC/CUDA/vLLM environment remains unchanged.
- The loaded model can be reused across Streamlit reruns.
- The OCR engine is hidden behind a typed provider protocol.
- A future provider can implement the same application-facing contract.

### Negative

- Local operation requires two processes and two Python environments.
- Windows-to-WSL path conversion and localhost forwarding must work.
- Worker health can be ready before first-request model loading completes.
- Cross-process failures require operator diagnostics at both service boundaries.
- Static typing in the Streamlit environment cannot resolve worker-only NaviDC imports.

## Rejected alternatives

### Install NaviDC in the Streamlit environment

Rejected because it couples a lightweight UI to the GPU dependency stack and discards the already validated runtime isolation.

### Run OCR in the Streamlit process

Rejected because Streamlit reruns would complicate model lifetime and GPU resource management.

### Use the upstream Gradio interface

Rejected because the requested product is a Streamlit application and does not require NaviDC's optional Gradio dependency set.

### Add PP-LayoutV3

Rejected for this version because NaviDC supplies its own layout analysis and no requirement justifies a second unvalidated layout pipeline.

## Review triggers

Revisit this decision if the application must support remote multi-user access, multiple GPUs, job persistence, provider authentication, or deployment outside this Windows/WSL machine.
