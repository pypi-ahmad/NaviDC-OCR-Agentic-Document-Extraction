# Configuration and artifact reference

## Application configuration

`.streamlit/config.toml` defines the checked application defaults.

| Setting | Value | Effect |
|---|---:|---|
| `server.port` | `8741` | Default Streamlit port |
| `server.maxUploadSize` | `100` | Upload limit in megabytes |
| `server.headless` | `true` | Runs without requiring a desktop browser |
| `client.showErrorDetails` | `none` | Hides Streamlit exception details from users |
| `browser.gatherUsageStats` | `false` | Disables Streamlit usage telemetry |

The remaining theme entries control the native light interface.

## Provider environment variables

| Variable | Default | Description |
|---|---|---|
| `NAVIDC_RUNTIME_DIR` | `/home/ahmad/projects/NaviDC-OCR` | Runtime directory inside WSL |
| `NAVIDC_PROVIDER_URL` | `http://127.0.0.1:8742` | Worker URL used by the adapter |
| `NAVIDC_PROVIDER_PORT` | `8742` | Port passed to a worker started by the adapter |

Set variables in the shell before launching. When changing the port, update both port variables consistently.

## Fixed worker configuration

The worker applies these values before importing `NaviOCR.engine`:

| NaviDC option | Value |
|---|---|
| `model_path` | `StarDoc-AI/NaviDC-OCR` |
| `BACKEND` | `vllm-async-engine` |
| `MAX_MODEL_LEN` | `8192` |
| `GPU_MEMORY_UTILIZATION` | `0.85` |
| `PDF_TOOLS_WORKER_MAX_NUM` | `1` |

The selected layout mode changes per serialized extraction request. Other model settings require a worker restart after a code change.

## Input reference

| Input | Handling |
|---|---|
| PDF | Validated with PyMuPDF; supports inclusive page selection |
| PNG | Converted to one-page RGB PDF |
| JPG/JPEG | Converted to one-page RGB PDF |
| TIF/TIFF | First frame converted to one-page RGB PDF |

The application rejects empty files, files above 100 MB, unsupported extensions, damaged inputs, password-protected PDFs, and zero-page PDFs.

## Artifact naming

The source stem is restricted to letters, numbers, dots, underscores, and hyphens, then limited to 80 characters. An empty result becomes `document`.

| Artifact | Name pattern |
|---|---|
| Markdown | `<stem>.md` |
| Annotated PDF | `<stem>_annotated.pdf` |
| HTML | `<stem>_view.html` |
| Bundle | `<stem>_extraction_bundle.zip` |

## Markdown artifact

The worker renders NaviDC blocks in original selected-page order. Each page begins with:

```markdown
<!-- Page 7 -->
```

The number refers to the page in the original source, not the selected PDF's temporary page index.

## Annotated PDF

NaviDC draws layout annotations on the selected source pages. Available labels, boxes, and order markers come from actual provider output.

## HTML

The HTML file is self-contained and renders the extracted Markdown as structured content:

- Markdown headings, paragraphs, lists, and tables become semantic HTML.
- NaviDC page markers create distinct document-style page sections.
- OCR content is HTML-escaped before rendering.
- No JavaScript or external asset request is required.
- A restrictive Content Security Policy permits only inline styles.

## Bundle layout

```text
<stem>_extraction_bundle.zip
├── <stem>.md
├── <stem>_annotated.pdf
├── <stem>_view.html
├── manifest.json
└── images/                 # Present only when extracted assets exist
```

See the [provider API reference](provider-api.md#final-manifest-reference) for the manifest schema.
