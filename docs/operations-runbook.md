# Operations runbook

## Service endpoints

| Service | Default endpoint | Purpose |
|---|---|---|
| Streamlit | `http://127.0.0.1:8741` | User interface |
| NaviDC provider | `http://127.0.0.1:8742` | Local health and extraction API |

## Start the application

Preferred Windows method:

1. Double-click `launch.cmd` in the repository root.
2. Open <http://localhost:8741> if the browser does not open.
3. Upload a document and run an extraction. The first extraction starts the provider and loads the model.

PowerShell method:

```powershell
Set-Location D:\AI\Github\NaviDC-OCR-Agentic-Document-Extraction
uv sync --all-groups
uv run streamlit run streamlit_app.py --server.port 8741
```

Leave the terminal open while using the application.

## Confirm service health

```powershell
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8741/_stcore/health).Content
Invoke-RestMethod http://127.0.0.1:8742/health
```

Expected application health is `ok`. Expected provider status is `ready` with model `StarDoc-AI/NaviDC-OCR`.

The provider does not exist until the first extraction or a manual start. A connection failure on port 8742 before that point is normal.

## Stop the application

Press `Ctrl+C` in the launcher or PowerShell window. If the Streamlit process remains, identify the exact listener before stopping it:

```powershell
Get-NetTCPConnection -LocalPort 8741 -State Listen | Select-Object OwningProcess
```

Then stop only the returned process ID:

```powershell
$appProcessId = (Get-NetTCPConnection -LocalPort 8741 -State Listen).OwningProcess
Stop-Process -Id $appProcessId
```

The WSL provider may remain available to avoid reloading the model. Stop it only when needed:

```powershell
wsl.exe -d Ubuntu-24.04 -- pkill -f 'uvicorn agentic_document_extraction.worker:app'
```

## Routine operating procedure

1. Prefer clear, straight scans at 200–300 DPI.
2. Use `Detection` first.
3. Select only the pages needed for the task.
4. For complex or long files, process smaller page ranges.
5. Review the annotated PDF for region and reading-order errors.
6. Download the ZIP bundle to retain all outputs and processing metadata.

## Troubleshooting

### Port 8741 is already in use

**Symptom:** Streamlit reports `Port 8741 is not available`.

```powershell
Get-NetTCPConnection -LocalPort 8741 -State Listen | Select-Object OwningProcess
```

If the process is the existing app, open <http://localhost:8741>. Otherwise, stop the exact process or explicitly choose another port for development. Production documentation and the launcher assume port 8741.

### Provider cannot start

**Symptom:** The UI says NaviDC-OCR could not start.

Check WSL and the runtime:

```powershell
wsl.exe -l -v
wsl.exe -d Ubuntu-24.04 -- test -x /home/ahmad/projects/NaviDC-OCR/.venv/bin/python
wsl.exe -d Ubuntu-24.04 -- nvidia-smi
```

All three commands must succeed. Confirm that the project remains at the expected Windows path or set the documented runtime environment variable.

### Provider is ready but extraction is slow

The first request may load the model into GPU memory. Later requests reuse the process. If extraction remains slow:

1. Reduce the selected page range.
2. Confirm no other GPU-heavy application is active with `nvidia-smi`.
3. Use `Detection` before trying `Segmentation`.
4. Avoid unnecessarily high-resolution source images.

### CUDA out of memory or worker exits

**Symptoms:** Extraction fails after model startup, provider health stops responding, or WSL reports GPU memory failure.

1. Close other GPU workloads.
2. Stop the provider using the exact command in “Stop the application.”
3. Confirm GPU memory is available with `wsl.exe -d Ubuntu-24.04 -- nvidia-smi`.
4. Restart the app and process fewer pages.

The checked worker configuration uses `GPU_MEMORY_UTILIZATION=0.85`, `MAX_MODEL_LEN=8192`, and one PDF worker for the 8 GB GPU.

### Upload is rejected

Confirm that:

- The file extension is PDF, PNG, JPG, JPEG, TIF, or TIFF.
- The file is not empty or larger than 100 MB.
- The PDF is not password-protected and contains at least one page.
- The image can be opened by Pillow.

### Results disappear

Results are session-scoped. They are cleared when the uploaded file, page range, or layout mode changes, or when the browser session ends. Download the ZIP before changing inputs.

### HTML text alignment is imperfect

The HTML artifact renders extracted Markdown in reading order and does not reproduce exact source coordinates. Use the annotated PDF to diagnose layout regions and bounding boxes.

## Configuration reference

| Environment variable | Default | Use |
|---|---|---|
| `NAVIDC_RUNTIME_DIR` | `/home/ahmad/projects/NaviDC-OCR` | NaviDC runtime directory inside WSL |
| `NAVIDC_PROVIDER_URL` | `http://127.0.0.1:8742` | URL used by the Streamlit process |
| `NAVIDC_PROVIDER_PORT` | `8742` | Port used when the adapter starts the worker |

Set variables before launching the app. If changing the port, keep `NAVIDC_PROVIDER_URL` and `NAVIDC_PROVIDER_PORT` consistent.

```powershell
$env:NAVIDC_PROVIDER_PORT = "8752"
$env:NAVIDC_PROVIDER_URL = "http://127.0.0.1:8752"
.\launch.cmd
```

These values are not secrets. Do not place credentials in this project.
