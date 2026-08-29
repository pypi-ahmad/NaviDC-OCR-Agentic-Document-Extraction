# Architecture

## System purpose

The application converts a scanned PDF or image into four local artifacts:

1. Layout-aware Markdown
2. A PDF annotated with OCR regions and reading order
3. A standalone HTML view rendered from the extracted Markdown
4. A ZIP bundle containing the artifacts, extracted images, and a manifest

The UI is comparable to an agentic document extraction workspace, while all inference remains on the local machine.

## Component map

```mermaid
flowchart LR
    Browser[Web browser] -->|localhost:8741| UI[Streamlit UI]
    UI --> Documents[Document handling]
    UI --> Client[NaviDC provider adapter]
    Client -->|HTTP multipart\nlocalhost:8742| Worker[FastAPI OCR worker]
    Worker --> Engine[NaviDC-OCR / vLLM]
    Engine --> GPU[NVIDIA GPU]
    Worker -->|ZIP response| Client
    UI --> Artifacts[Artifact generation]
    Documents --> Artifacts
    Client --> Artifacts
    Artifacts --> Downloads[MD / PDF / HTML / ZIP]
```

## Modules

| Module | Responsibility |
|---|---|
| `streamlit_app.py` | Page configuration, sidebar controls, previews, progress, result tabs, session state, and downloads |
| `documents.py` | Upload validation, PDF inspection, image-to-PDF normalization, inclusive page selection, safe filenames, and preview rendering |
| `provider.py` | Typed provider boundary, worker lifecycle, health checks, HTTP request, timeout handling, and provider ZIP parsing |
| `worker.py` | FastAPI endpoints, fixed NaviDC configuration, GPU request serialization, OCR execution, and result packaging |
| `artifacts.py` | Artifact names, manifest, final ZIP, page rasterization, and escaped OCR text overlays |

## Runtime separation

The system uses two Python environments:

| Process | Environment | Reason |
|---|---|---|
| Streamlit | Repository `.venv`, managed by `uv` | Small, current application environment without GPU libraries |
| OCR worker | `/home/ahmad/projects/NaviDC-OCR/.venv` in WSL | Python 3.12 environment containing NaviDC-OCR, PyTorch, CUDA, and vLLM |

On Windows, the provider adapter converts the repository `src` path with `wslpath` and adds it to the worker's `PYTHONPATH`. The worker can therefore load the adapter module without installing the Streamlit project into the NaviDC environment.

## Extraction sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit
    participant Doc as Document handling
    participant API as OCR worker
    participant OCR as NaviDC-OCR
    participant Build as Artifact builder

    User->>UI: Upload PDF or image
    UI->>Doc: Validate and normalize
    Doc-->>UI: Metadata and normalized PDF
    User->>UI: Select inclusive range and layout mode
    UI->>Doc: Copy selected pages in source order
    UI->>API: POST /extract (selected PDF)
    API->>OCR: aio_do_parse
    OCR-->>API: Markdown model output, middle JSON, annotations, images
    API-->>UI: Provider ZIP
    UI->>Build: Build visual HTML, manifest, and bundle
    Build-->>UI: Downloadable artifacts
    UI-->>User: Preview and download results
```

## Data lifecycle

- Streamlit reads the uploaded bytes into the active session.
- Images are normalized to a one-page PDF in memory. For TIFF, only the first frame is used.
- Only selected PDF pages are sent to the worker.
- The worker creates a request-scoped temporary directory.
- The worker returns an in-memory ZIP and deletes its temporary directory when the request ends.
- Final artifacts remain in Streamlit session state until the selection changes or the session ends.
- The application does not implement persistent upload or result storage.

## Concurrency and capacity

An `asyncio.Lock` in the worker permits one active extraction at a time. This prevents simultaneous vLLM jobs from competing for the machine's 8 GB GPU. Requests may wait behind an active extraction.

The UI warns for selections above 25 pages, but does not reject them. Actual capacity depends on page complexity, scan resolution, and available GPU memory.

## Security boundaries

- The OCR worker explicitly binds to `127.0.0.1`. Streamlit exposure follows its server binding configuration; use the application only on a trusted local network unless `server.address` is restricted.
- The UI limits uploads to 100 MB and validates the file with PyMuPDF or Pillow.
- Password-protected and zero-page PDFs are rejected.
- Provider errors shown to users are bounded and do not include stack traces.
- Generated HTML escapes OCR content and includes a restrictive Content Security Policy.
- Provider configuration comes from documented environment variables; credentials are not required or displayed.
- Temporary OCR files are request-scoped.

This is a single-user local application. It does not implement authentication, authorization, rate limiting, or hostile multi-tenant isolation.

## Known constraints

- The worker model configuration is fixed at process startup.
- The provider API is local and intentionally not a public network API.
- A failed worker writes no result artifact; there is no synthetic OCR fallback.
- HTML preserves Markdown structure, tables, reading order, and page boundaries in a document-style view. It does not embed the source PDF.
- OCR accuracy remains dependent on the source scan and model behavior.
