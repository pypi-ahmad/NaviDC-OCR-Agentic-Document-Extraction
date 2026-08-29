# Tutorial: Run your first local extraction

This tutorial takes a new user from a prepared checkout to a complete extraction bundle.

**Time:** About 10 minutes, plus first model-load time

**Outcome:** Markdown, annotated PDF, standalone HTML, and ZIP artifacts for the included smoke PDF

## Prerequisites

Confirm that you have:

- Windows 11
- WSL 2 with the `Ubuntu-24.04` distribution
- `uv` available in PowerShell
- The NaviDC runtime at `/home/ahmad/projects/NaviDC-OCR`
- An NVIDIA GPU visible inside WSL

Check the tools:

```powershell
uv --version
wsl.exe -d Ubuntu-24.04 -- nvidia-smi
```

Both commands should exit successfully.

## 1. Prepare the Streamlit environment

Open PowerShell in the repository and synchronize dependencies:

```powershell
Set-Location D:\AI\Github\NaviDC-OCR-Agentic-Document-Extraction
uv sync --all-groups
```

This creates the project-local `.venv`. It does not change the separate NaviDC environment.

## 2. Start the application

Double-click `launch.cmd`, or run:

```powershell
.\launch.cmd
```

Open <http://localhost:8741> when the terminal says Streamlit is ready.

## 3. Upload the sample

1. Select **Browse files** in the sidebar.
2. Choose `input/navidc-smoke-test.pdf`.
3. Confirm that the sidebar shows one page and the main pane renders the source preview.

At this checkpoint, only document validation and preview rendering have run. The OCR model has not run yet.

## 4. Extract the document

1. Leave the page range at page 1.
2. Leave **Layout mode** set to **Detection**.
3. Select **Extract document**.

The first request starts the local worker and may take several minutes while vLLM loads the model. Progress then moves through OCR and artifact generation.

## 5. Inspect the results

Use each result tab:

- **Rendered Markdown** checks headings, paragraphs, and reading order.
- **Raw Markdown** shows the exact downloadable text and source-page marker.
- **Annotated PDF** shows detected regions and reading order.
- **Original-style HTML** preserves the scan visually and adds selectable OCR text.

If a tab does not appear, follow the [operations runbook](operations-runbook.md#troubleshooting).

## 6. Download the bundle

Select **Download bundle** in the sidebar. Open the ZIP and confirm it contains:

```text
navidc-smoke-test.md
navidc-smoke-test_annotated.pdf
navidc-smoke-test_view.html
manifest.json
```

An `images/` directory appears only when NaviDC extracts image assets.

Open `manifest.json` and confirm the source filename, selected range, provider, model, layout mode, timestamp, and artifact names.

## What you learned

You prepared the lightweight application environment, started both local processes, selected source pages, ran NaviDC-OCR, reviewed grounding information, and retained a reproducible artifact bundle.

Next, use [How to improve extraction accuracy](how-to-improve-accuracy.md) for difficult scans or the [operator runbook](operations-runbook.md) for service management.
