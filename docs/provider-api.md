# Local provider API reference

## Scope

The OCR worker exposes a small loopback-only HTTP API for the Streamlit process. It is implemented by [`worker.py`](../src/agentic_document_extraction/worker.py) and normally listens at `http://127.0.0.1:8742`.

The worker disables FastAPI's interactive documentation routes. This page is the API reference.

## `GET /health`

Checks whether the worker process is ready to accept an extraction request. A ready response does not imply that the model has already been loaded into GPU memory; model loading can occur during the first extraction.

### Response

Status: `200 OK`

```json
{
  "status": "ready",
  "provider": "NaviDC-OCR",
  "model": "StarDoc-AI/NaviDC-OCR"
}
```

### PowerShell example

```powershell
Invoke-RestMethod http://127.0.0.1:8742/health
```

## `POST /extract`

Runs NaviDC-OCR on an already normalized and page-selected PDF.

### Request

Content type: `multipart/form-data`

| Field | Type | Required | Constraints |
|---|---|---:|---|
| `document` | File | Yes | Non-empty PDF, at most 100 MB |
| `source_pages` | JSON string | Yes | Non-empty array of integers greater than or equal to 1 |
| `layout_mode` | String | Yes | `Detection` or `Segmentation` |

`source_pages` maps each page in the submitted PDF back to its one-based page number in the original document. Its order should match the submitted PDF page order.

### Python example

```python
import json
from pathlib import Path

import httpx

pdf = Path("input/navidc-smoke-test.pdf")
with httpx.Client(timeout=httpx.Timeout(1800, connect=10)) as client:
    response = client.post(
        "http://127.0.0.1:8742/extract",
        files={"document": (pdf.name, pdf.read_bytes(), "application/pdf")},
        data={
            "source_pages": json.dumps([1]),
            "layout_mode": "Detection",
        },
    )
    response.raise_for_status()
    Path("provider-result.zip").write_bytes(response.content)
```

### Success response

Status: `200 OK`

Content type: `application/zip`

| Entry | Description |
|---|---|
| `result.md` | OCR Markdown with `<!-- Page N -->` source-page markers |
| `annotated.pdf` | Selected source pages with NaviDC layout annotations |
| `middle.json` | NaviDC intermediate layout representation |
| `images/*` | Images extracted by NaviDC, when present |

The provider adapter validates the three required entries before accepting the result.

### Error responses

| Status | Condition | Example detail |
|---:|---|---|
| `422` | Unsupported layout mode | `Choose Detection or Segmentation layout mode.` |
| `422` | Missing or invalid page mapping | `The selected page range is invalid.` |
| `422` | Empty or oversized document | `The document is empty or exceeds 100 MB.` |
| `500` | NaviDC processing failure | Generic retry guidance without an internal stack trace |

FastAPI may also return its standard `422` response when a required multipart field is missing.

## Client behavior

`NaviDcProvider` uses these operational limits:

- Health request timeout: 2 seconds
- Worker startup window: 45 seconds by default
- Extraction timeout: 1,800 seconds
- Connection timeout: 10 seconds
- One worker URL configured by `NAVIDC_PROVIDER_URL`

The worker serializes extraction calls. HTTP clients must tolerate queueing and model startup within the extraction timeout.

## Final manifest reference

The final user-facing ZIP is assembled by the Streamlit process, not the worker. Its `manifest.json` contains:

```json
{
  "source_filename": "invoice.pdf",
  "source_type": "pdf",
  "source_sha256": "...",
  "selected_page_range": {"start": 2, "end": 4},
  "total_source_page_count": 7,
  "artifacts": {
    "markdown": "invoice.md",
    "annotated_pdf": "invoice_annotated.pdf",
    "html": "invoice_view.html"
  },
  "generated_at": "2026-08-29T12:30:00+00:00",
  "ocr_provider": "NaviDC-OCR",
  "ocr_model": "StarDoc-AI/NaviDC-OCR",
  "layout_mode": "Detection"
}
```

`generated_at` is an ISO 8601 UTC timestamp. The SHA-256 digest covers the original uploaded bytes.
