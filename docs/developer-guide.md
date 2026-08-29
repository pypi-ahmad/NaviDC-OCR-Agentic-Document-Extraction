# Developer guide

## Development model

The repository contains a lightweight Streamlit application and an isolated WSL OCR worker. Make application changes in this repository. Make NaviDC engine changes only in its separate runtime repository when the task explicitly requires them.

## Set up the application environment

From PowerShell at the repository root:

```powershell
uv sync --all-groups
```

This creates or updates `.venv` from `pyproject.toml` and `uv.lock`. Use `uv` for all dependency and command execution.

The configured Python requirement is 3.12 or newer. `.python-version` selects Python 3.14.7 for the Streamlit environment on this machine. Worker code must remain compatible with Python 3.12 because it is imported by the NaviDC runtime.

## Run in development

```powershell
uv run streamlit run streamlit_app.py --server.port 8741
```

Alternatively, double-click `launch.cmd`. Streamlit reloads the application when source files change.

The provider starts lazily on the first extraction. Test its health with:

```powershell
Invoke-RestMethod http://127.0.0.1:8742/health
```

## Source map

```text
.
├── streamlit_app.py
├── launch.cmd
├── pyproject.toml
├── .streamlit/config.toml
├── src/agentic_document_extraction/
│   ├── artifacts.py
│   ├── documents.py
│   ├── provider.py
│   └── worker.py
├── tests/test_core.py
├── docs/
├── research/
└── knowledge-base/
```

## Core contracts

### Documents

`inspect_document()` is the validation boundary. It returns an immutable `DocumentInfo` containing metadata, normalized PDF bytes, and the original upload digest.

`select_pdf_pages()` accepts one-based inclusive page numbers and emits a new PDF in source order. Keep range validation in `validate_page_range()` so the UI and tests share one rule.

### Provider

Code outside `provider.py` should depend on the `OcrProvider` protocol or `ProviderOutput`, not NaviDC internals. The Streamlit process must not import Torch, vLLM, or `NaviOCR`.

The worker is the only application module that imports `NaviOCR`. Its configuration must be applied before importing `NaviOCR.engine`.

### Artifacts

`BundleInput` is the complete input to final packaging. `build_bundle()` owns archive layout and `build_manifest()` owns manifest fields.

`build_original_style_html()` must continue to escape OCR text. Do not insert model-produced HTML directly into the standalone document or Streamlit.

### Session state

The UI keys an extraction result by source SHA-256, selected range, and layout mode. Changing any of those inputs invalidates the stored result.

## Add a dependency

Runtime dependency:

```powershell
uv add package-name
```

Development dependency:

```powershell
uv add --dev package-name
```

Do not add NaviDC, Torch, CUDA, or vLLM to the application environment.

## Test and validate

Run the focused gates:

```powershell
uv run pytest
uv run ruff format --check src tests streamlit_app.py
uv run ruff check src tests streamlit_app.py
uv run ty check src
```

The ty configuration excludes `worker.py` because its NaviDC and FastAPI imports exist only in the isolated WSL environment. Validate worker syntax with its actual Python interpreter:

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc 'PYTHONPATH=/mnt/d/AI/Github/NaviDC-OCR-Agentic-Document-Extraction/src /home/ahmad/projects/NaviDC-OCR/.venv/bin/python -m py_compile /mnt/d/AI/Github/NaviDC-OCR-Agentic-Document-Extraction/src/agentic_document_extraction/worker.py'
```

Check the live app:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8741/_stcore/health
```

## Test coverage

`tests/test_core.py` currently verifies:

- Acceptance and rejection rules for inclusive page ranges
- Selected PDF page count and source order
- ZIP entry composition and manifest values

When changing upload normalization, HTML overlay generation, or provider error handling, add focused tests for the changed boundary.

## Change checklist

1. Confirm the relevant behavior in source and existing research.
2. Write or update a focused test when the behavior is testable without the GPU.
3. Keep application and GPU dependencies isolated.
4. Run the narrow checks above.
5. For provider changes, run one real extraction with `input/navidc-smoke-test.pdf`.
6. Update the appropriate document under `docs/` if a contract, command, or operational limit changed.
