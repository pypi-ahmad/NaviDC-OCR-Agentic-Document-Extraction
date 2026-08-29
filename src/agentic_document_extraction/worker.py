from __future__ import annotations

import asyncio
import io
import json
import tempfile
import zipfile
from pathlib import Path

import NaviOCR.config as CONFIG
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import Response

CONFIG.update(
    [
        "model_path=StarDoc-AI/NaviDC-OCR",
        "BACKEND=vllm-async-engine",
        "MAX_MODEL_LEN=8192",
        "GPU_MEMORY_UTILIZATION=0.85",
        "PDF_TOOLS_WORKER_MAX_NUM=1",
    ]
)

from NaviOCR.engine import aio_do_parse  # noqa: E402
from NaviOCR.src.vlm_middle_json_mkcontent import union_make  # noqa: E402

app = FastAPI(title="Local NaviDC-OCR provider", docs_url=None, redoc_url=None)
_extraction_lock = asyncio.Lock()


@app.get("/health")
async def health() -> dict[str, str]:
    """Report worker readiness and the configured NaviDC model."""
    return {"status": "ready", "provider": "NaviDC-OCR", "model": CONFIG.model_path}


@app.post("/extract")
async def extract(
    document: UploadFile,
    source_pages: str = Form(...),
    layout_mode: str = Form("Detection"),
) -> Response:
    """Run OCR for an uploaded page-selected PDF.

    Args:
        document: Multipart PDF upload, limited to 100 MB.
        source_pages: JSON array mapping submitted pages to source page numbers.
        layout_mode: NaviDC layout mode, either ``Detection`` or ``Segmentation``.

    Returns:
        ZIP response containing Markdown, annotations, middle JSON, and images.

    Raises:
        HTTPException: With status 422 for invalid input or 500 when NaviDC
            cannot complete extraction.
    """
    if layout_mode not in {"Detection", "Segmentation"}:
        raise HTTPException(status_code=422, detail="Choose Detection or Segmentation layout mode.")
    try:
        page_numbers = json.loads(source_pages)
        if (
            not isinstance(page_numbers, list)
            or not page_numbers
            or not all(isinstance(value, int) and value >= 1 for value in page_numbers)
        ):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=422, detail="The selected page range is invalid.") from None
    pdf_bytes = await document.read()
    if not pdf_bytes or len(pdf_bytes) > 100 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="The document is empty or exceeds 100 MB.")

    async with _extraction_lock:
        CONFIG.LAYOUT_MODE = layout_mode
        try:
            archive = await _run_extraction(pdf_bytes, page_numbers)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "NaviDC-OCR could not process this document. Try fewer pages or a clearer scan."
                ),
            ) from exc
    return Response(archive, media_type="application/zip")


async def _run_extraction(pdf_bytes: bytes, page_numbers: list[int]) -> bytes:
    with tempfile.TemporaryDirectory(prefix="navidc-") as temporary:
        output_root = Path(temporary)
        results = await aio_do_parse(str(output_root), ["document"], [pdf_bytes], [None])
        result_dir = output_root / "document"
        middle = results[0]
        pages = middle.get("pdf_info", [])
        markdown_parts = []
        for index, page in enumerate(pages):
            source_page = page_numbers[index] if index < len(page_numbers) else index + 1
            markdown_parts.append(f"<!-- Page {source_page} -->\n\n{union_make([page], 'images')}")
        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("result.md", "\n\n".join(markdown_parts).strip() + "\n")
            archive.writestr("middle.json", json.dumps(middle, ensure_ascii=False, indent=2))
            archive.write(result_dir / "document_layout.pdf", "annotated.pdf")
            image_dir = result_dir / "images"
            if image_dir.exists():
                for path in image_dir.iterdir():
                    if path.is_file():
                        archive.write(path, f"images/{path.name}")
        return archive_buffer.getvalue()
