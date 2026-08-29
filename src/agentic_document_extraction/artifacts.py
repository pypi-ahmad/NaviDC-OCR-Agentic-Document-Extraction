from __future__ import annotations

import base64
import html
import io
import json
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

from .documents import render_pdf_pages, safe_stem


@dataclass(frozen=True, slots=True)
class BundleInput:
    """Inputs required to create the final extraction bundle.

    Attributes:
        source_filename: Original uploaded base filename.
        source_type: Normalized source type.
        source_sha256: Digest of the original upload.
        total_source_pages: Page count before selection.
        start_page: First selected source page.
        end_page: Last selected source page.
        provider: Human-readable OCR provider name.
        provider_model: Model identifier reported in the manifest.
        layout_mode: Layout strategy used for extraction.
        markdown: Extracted Markdown bytes.
        annotated_pdf: Provider-generated annotated PDF bytes.
        html: Standalone visual HTML bytes.
        images: Optional provider-extracted image assets by filename.
        generated_at: Time recorded in the manifest.
    """

    source_filename: str
    source_type: str
    source_sha256: str
    total_source_pages: int
    start_page: int
    end_page: int
    provider: str
    provider_model: str
    layout_mode: str
    markdown: bytes
    annotated_pdf: bytes
    html: bytes
    images: dict[str, bytes] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def artifact_names(source_filename: str) -> dict[str, str]:
    """Derive all user-facing artifact names from a source filename.

    Args:
        source_filename: Original uploaded filename.

    Returns:
        Mapping for ``markdown``, ``annotated_pdf``, ``html``, and ``bundle``.
    """
    stem = safe_stem(source_filename)
    return {
        "markdown": f"{stem}.md",
        "annotated_pdf": f"{stem}_annotated.pdf",
        "html": f"{stem}_view.html",
        "bundle": f"{stem}_extraction_bundle.zip",
    }


def build_manifest(item: BundleInput) -> dict[str, Any]:
    """Build serializable provenance metadata for an extraction.

    Args:
        item: Complete artifact and source metadata.

    Returns:
        Manifest mapping suitable for JSON serialization.
    """
    names = artifact_names(item.source_filename)
    return {
        "source_filename": item.source_filename,
        "source_type": item.source_type,
        "source_sha256": item.source_sha256,
        "selected_page_range": {"start": item.start_page, "end": item.end_page},
        "total_source_page_count": item.total_source_pages,
        "artifacts": {key: names[key] for key in ("markdown", "annotated_pdf", "html")},
        "generated_at": item.generated_at.astimezone(UTC).isoformat(),
        "ocr_provider": item.provider,
        "ocr_model": item.provider_model,
        "layout_mode": item.layout_mode,
    }


def build_bundle(item: BundleInput) -> bytes:
    """Package extraction artifacts, metadata, and images into a ZIP archive.

    Args:
        item: Complete bundle input.

    Returns:
        In-memory ZIP bytes. Image paths are reduced to safe base filenames.
    """
    names = artifact_names(item.source_filename)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(names["markdown"], item.markdown)
        archive.writestr(names["annotated_pdf"], item.annotated_pdf)
        archive.writestr(names["html"], item.html)
        archive.writestr("manifest.json", json.dumps(build_manifest(item), indent=2) + "\n")
        for name, content in sorted(item.images.items()):
            clean_name = PurePosixPath(name).name
            if clean_name:
                archive.writestr(f"images/{clean_name}", content)
    return output.getvalue()


def build_original_style_html(
    pdf_bytes: bytes, middle_json: dict[str, Any], source_pages: list[int], title: str
) -> bytes:
    """Create a standalone visual document with selectable OCR overlays.

    The rendered source pages are embedded as data URLs. OCR text and labels
    are HTML-escaped before insertion, and the document includes a restrictive
    Content Security Policy.

    Args:
        pdf_bytes: Selected source pages as a PDF.
        middle_json: NaviDC intermediate data containing page sizes and blocks.
        source_pages: Original one-based page number for each selected page.
        title: Human-readable document title.

    Returns:
        UTF-8 encoded standalone HTML.
    """
    page_images = render_pdf_pages(pdf_bytes)
    page_info = middle_json.get("pdf_info", [])
    sections: list[str] = []
    for index, image_bytes in enumerate(page_images):
        info = (
            page_info[index]
            if index < len(page_info) and isinstance(page_info[index], dict)
            else {}
        )
        size = info.get("page_size") or [1, 1]
        width, height = _positive_float(size, 0), _positive_float(size, 1)
        overlays = "".join(
            _block_overlay(block, width, height) for block in info.get("para_blocks", [])
        )
        page_number = source_pages[index] if index < len(source_pages) else index + 1
        encoded = base64.b64encode(image_bytes).decode("ascii")
        sections.append(
            f'<section class="page" aria-label="Source page {page_number}">'
            f'<img src="data:image/jpeg;base64,{encoded}" alt="Scanned source page {page_number}">'
            f'<div class="overlay">{overlays}</div>'
            f'<span class="page-number">Page {page_number}</span>'
            "</section>"
        )
    safe_title = html.escape(title)
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy"
 content="default-src 'none'; img-src data:; style-src 'unsafe-inline'">
<title>{safe_title}</title><style>
:root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; padding: 32px 16px; background: #eeeae2; color: #292720; }}
header {{ max-width: 1000px; margin: 0 auto 18px; }} h1 {{ font-size: 18px; margin: 0; }}
.page {{ position: relative; max-width: 1000px; margin: 0 auto 28px; background: white;
 box-shadow: 0 8px 28px #29272024; }}
.page img {{ display: block; width: 100%; height: auto; }}
.overlay {{ position: absolute; inset: 0; }}
.region {{ position: absolute; color: transparent; white-space: pre-wrap; overflow: hidden;
 line-height: 1.15; user-select: text; }}
.region:hover {{ outline: 2px solid #e59b45; background: #e59b451a; }}
.page-number {{ position: absolute; right: 10px; bottom: 8px; background: #292720c9;
 color: white; padding: 3px 7px; border-radius: 4px; font-size: 11px; }}
</style></head><body><header><h1>{safe_title}</h1></header>{"".join(sections)}</body></html>"""
    return document.encode("utf-8")


def _positive_float(values: Any, index: int) -> float:
    try:
        value = float(values[index])
        return value if value > 0 else 1.0
    except (IndexError, TypeError, ValueError):
        return 1.0


def _block_overlay(block: Any, page_width: float, page_height: float) -> str:
    if not isinstance(block, dict):
        return ""
    bbox = block.get("bbox")
    text = _collect_text(block)
    if not text or not isinstance(bbox, list) or len(bbox) < 4:
        return ""
    try:
        x0, y0, x1, y1 = (float(value) for value in bbox[:4])
    except (TypeError, ValueError):
        return ""
    left, top = max(0.0, x0 / page_width * 100), max(0.0, y0 / page_height * 100)
    width, height = max(0.1, (x1 - x0) / page_width * 100), max(0.1, (y1 - y0) / page_height * 100)
    label = html.escape(str(block.get("type", "text")))
    return (
        f'<span class="region" title="{label}" style="left:{left:.3f}%;top:{top:.3f}%;'
        f'width:{width:.3f}%;height:{height:.3f}%">{html.escape(text)}</span>'
    )


def _collect_text(value: Any) -> str:
    parts: list[str] = []
    if isinstance(value, dict):
        content = value.get("content")
        if isinstance(content, str) and value.get("type") not in {"image", "table"}:
            parts.append(content)
        for key in ("lines", "spans", "blocks", "children"):
            if key in value:
                nested = _collect_text(value[key])
                if nested:
                    parts.append(nested)
    elif isinstance(value, list):
        parts.extend(filter(None, (_collect_text(item) for item in value)))
    return "\n".join(parts)
