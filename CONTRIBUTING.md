# Contributing

This guide is for developers changing the local Streamlit application or its NaviDC-OCR adapter.

## Before you begin

- Read the [architecture](docs/architecture.md) and [ADR-001](docs/adr/001-isolated-ocr-worker.md).
- Install `uv` on Windows.
- Keep the application and NaviDC GPU environments separate.
- Preserve existing research, knowledge-base material, and user-generated files.
- Never commit credentials, local model caches, uploads, generated output, or virtual environments.

## Set up a development environment

```powershell
Set-Location D:\AI\Github\NaviDC-OCR-Agentic-Document-Extraction
uv sync --all-groups
```

Run the application:

```powershell
uv run streamlit run streamlit_app.py --server.port 8741
```

See the [developer guide](docs/developer-guide.md) for the source map and runtime details.

## Make a change

1. Identify the narrowest module responsible for the behavior.
2. Add or update a focused test when the behavior can be tested without the GPU.
3. Keep public functions typed and documented with Google-style docstrings.
4. Keep user-facing errors concise and free of stack traces, paths, and secrets.
5. Update documentation when changing commands, ports, limits, artifact formats, or API contracts.

Do not add Torch, CUDA, vLLM, or NaviDC to the Streamlit project dependencies. Those packages belong to the isolated WSL runtime.

## Validate the change

```powershell
uv run pytest
uv run ruff format --check src tests streamlit_app.py
uv run ruff check src tests streamlit_app.py
uv run ty check src
```

Worker code must also compile under the NaviDC Python 3.12 environment:

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc 'PYTHONPATH=/mnt/d/AI/Github/NaviDC-OCR-Agentic-Document-Extraction/src /home/ahmad/projects/NaviDC-OCR/.venv/bin/python -m py_compile /mnt/d/AI/Github/NaviDC-OCR-Agentic-Document-Extraction/src/agentic_document_extraction/worker.py'
```

For provider changes, complete one real extraction using `input/navidc-smoke-test.pdf` and inspect the Markdown, annotated PDF, HTML, and ZIP manifest.

## Code conventions

- Target Python 3.12 syntax because the worker runs in Python 3.12.
- Use immutable, slotted dataclasses for artifact and document value objects.
- Use one-based inclusive page numbers at the UI boundary.
- Use bytes at document and artifact boundaries.
- Convert engine-specific output only inside the provider boundary.
- Escape OCR text before placing it in HTML.
- Use temporary directories for request-scoped worker files.
- Prefer small functions over new framework layers.

## Documentation conventions

- Use GitHub Flavored Markdown and relative links.
- Put learning material in tutorials, task recipes in how-to guides, contracts in reference pages, and design reasoning in explanations or ADRs.
- Specify a language for fenced code blocks.
- Keep examples copy-pasteable and document expected results.
- Run the local-link validation described in the [documentation coverage report](docs/documentation-coverage.md).
