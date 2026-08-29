# Documentation coverage report

## Summary

| Area | Coverage | Evidence |
|---|---:|---|
| Python application modules | 5/5 | Module responsibilities documented in architecture and developer guide |
| Public Python classes | 9/9 | Google-style class docstrings |
| Public Python functions and methods | 19/19 | Google-style docstrings, including errors on fallible boundaries |
| FastAPI endpoints | 2/2 | Prose reference and OpenAPI 3.1 contract |
| Configuration surfaces | 3/3 | Streamlit config, environment variables, and fixed worker config |
| User artifact types | 4/4 | Markdown, annotated PDF, HTML, and ZIP reference |
| Diátaxis quadrants | 4/4 | Tutorial, how-to, reference, and explanation pages |

Coverage counts exclude private helpers prefixed with `_`, tests, generated caches, and Streamlit's declarative top-level widget code.

## Documentation map

| Type | Document | Reader goal |
|---|---|---|
| Tutorial | [First extraction](tutorial-first-extraction.md) | Complete a successful local OCR workflow |
| How-to | [Improve accuracy](how-to-improve-accuracy.md) | Diagnose and improve difficult results |
| How-to | [Operations runbook](operations-runbook.md) | Start, stop, monitor, and recover services |
| Reference | [Configuration and artifacts](configuration-and-artifacts.md) | Look up limits, settings, and output formats |
| Reference | [Provider API](provider-api.md) | Integrate with the worker contract |
| Reference | [OpenAPI 3.1](openapi.yaml) | Consume the machine-readable HTTP contract |
| Explanation | [Architecture](architecture.md) | Understand components, flow, and boundaries |
| Explanation | [ADR-001](adr/001-isolated-ocr-worker.md) | Understand runtime isolation trade-offs |
| Project policy | [Contributing](../CONTRIBUTING.md) | Change the code safely and consistently |
| Project policy | [Security](../SECURITY.md) | Understand the local trust model |

## Documentation style

- Markdown: GitHub Flavored Markdown with relative links
- Python: Google-style docstrings
- API: OpenAPI 3.1 plus task-oriented prose
- Diagrams: Mermaid source embedded in Markdown
- Commands: PowerShell unless the command intentionally runs inside WSL

## Validation

The documentation set is checked by:

1. Resolving all relative Markdown links against their containing file.
2. Parsing `docs/openapi.yaml` and checking the required endpoints.
3. Running Python tests, Ruff formatting/lint, and ty.
4. Compiling worker source with the NaviDC Python 3.12 interpreter.
5. Running module doctest discovery for application modules that do not require NaviDC.

## Maintenance triggers

Update documentation when changing:

- Ports, environment variables, runtime paths, or model configuration
- Supported input types, size limits, or page behavior
- Provider fields, response archive entries, or HTTP errors
- Manifest fields or artifact names
- Python version, dependencies, or validation commands
- Security assumptions, persistence, concurrency, or network exposure
