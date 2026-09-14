"""Artifact packaging and display conversion: standalone HTML, markdown, and ZIP bundles.

This module is responsible for packaging OCR outputs, structured extractions,
audit logs, and quality reports into self-contained zip archives, standalone
HTML views, and sanitized Markdown. It must not execute OCR, call language
models, or modify input documents. Open schemas.py or grounding.py next to
see how structured data and evidence blocks are prepared.
"""

from __future__ import annotations

import html
import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import Any

from markdown_it import MarkdownIt

from .documents import safe_stem

# Regex boundaries: NaviDC-OCR outputs raw HTML table elements embedded in
# Markdown, and worker._run_extraction demarcates pages with `<!-- Page N -->`.
# Both are parsed here to convert raw tables into Markdown and section off pages.
_HTML_TABLE_PATTERN = re.compile(r"<table\b[^>]*>.*?</table>", re.IGNORECASE | re.DOTALL)
_PAGE_MARKER_PATTERN = re.compile(r"<!--\s*Page\s+(\d+)\s*-->", re.IGNORECASE)


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
    structured_json: bytes | None = None
    schema_json: bytes | None = None
    quality_json: bytes | None = None
    review_json: bytes | None = None
    field_guide: bytes | None = None
    semantic_model: str | None = None
    reasoning_effort: str | None = None
    schema_hash: str | None = None
    accuracy_policy: str | None = None
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
    artifacts = {key: names[key] for key in ("markdown", "annotated_pdf", "html")}
    for key, filename, content in (
        ("structured_extraction", "extraction.json", item.structured_json),
        ("schema", "schema.json", item.schema_json),
        ("quality_report", "quality-report.json", item.quality_json),
        ("review_audit", "review-audit.json", item.review_json),
        ("field_guide", "field-guide.md", item.field_guide),
    ):
        if content is not None:
            artifacts[key] = filename
    return {
        "source_filename": item.source_filename,
        "source_type": item.source_type,
        "source_sha256": item.source_sha256,
        "selected_page_range": {"start": item.start_page, "end": item.end_page},
        "total_source_page_count": item.total_source_pages,
        "artifacts": artifacts,
        "generated_at": item.generated_at.astimezone(UTC).isoformat(),
        "ocr_provider": item.provider,
        "ocr_model": item.provider_model,
        "layout_mode": item.layout_mode,
        "accuracy_policy": item.accuracy_policy,
        "structured_extraction": {
            "model": item.semantic_model,
            "reasoning_effort": item.reasoning_effort,
            "schema_hash": item.schema_hash,
        },
    }


def build_bundle(item: BundleInput) -> bytes:
    """Package extraction artifacts, metadata, and images into a ZIP archive.

    Args:
        item: Complete bundle input.

    Returns:
        In-memory ZIP bytes. Image paths are reduced to safe base filenames.
    """
    # Bundle layout on disk: stores core artifacts alongside optional schema,
    # quality, and audit manifests. Extracted image keys are sanitized with
    # PurePosixPath(name).name to strip directory traversal sequences before
    # storing them under the images/ folder.
    names = artifact_names(item.source_filename)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(names["markdown"], item.markdown)
        archive.writestr(names["annotated_pdf"], item.annotated_pdf)
        archive.writestr(names["html"], item.html)
        archive.writestr("manifest.json", json.dumps(build_manifest(item), indent=2) + "\n")
        optional = {
            "extraction.json": item.structured_json,
            "schema.json": item.schema_json,
            "quality-report.json": item.quality_json,
            "review-audit.json": item.review_json,
            "field-guide.md": item.field_guide,
        }
        for name, content in optional.items():
            if content is not None:
                archive.writestr(name, content)
        for name, content in sorted(item.images.items()):
            clean_name = PurePosixPath(name).name
            if clean_name:
                archive.writestr(f"images/{clean_name}", content)
    return output.getvalue()


def build_html(markdown: str, title: str) -> bytes:
    """Convert extracted Markdown into a safe, standalone document view.

    Page markers become visible document sections. NaviDC HTML tables are
    normalized to Markdown tables, while other raw provider HTML is escaped.
    The source PDF and its page images are intentionally not embedded.
    """
    # Security boundary: raw HTML is escaped and rendered with a restrictive
    # Content-Security-Policy (default-src 'none'; style-src 'unsafe-inline')
    # to neutralize any script or network exfiltration payloads embedded in
    # untrusted document text.
    renderer = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table")
    parts = _PAGE_MARKER_PATTERN.split(markdown)
    sections: list[str] = []
    if parts[0].strip():
        content = renderer.render(markdown_for_display(parts[0]))
        sections.append(f'<section class="page">{content}</section>')
    for index in range(1, len(parts), 2):
        page_number = int(parts[index])
        source = parts[index + 1] if index + 1 < len(parts) else ""
        content = renderer.render(markdown_for_display(source))
        sections.append(
            f'<section class="page" aria-label="Page {page_number}">'
            f'<div class="page-label">Page {page_number}</div>{content}</section>'
        )
    if not sections:
        sections.append('<section class="page"><p>No extracted content.</p></section>')
    safe_title = html.escape(title)
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy"
 content="default-src 'none'; style-src 'unsafe-inline'">
<title>{safe_title}</title><style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 32px 18px 64px; background: #111216; color: #e9e8f4; }}
header, .page {{ max-width: 920px; margin-left: auto; margin-right: auto; }}
header {{ margin-bottom: 18px; color: #a5f3fc; }} header h1 {{ font-size: 18px; margin: 0; }}
.page {{ position: relative; margin-bottom: 24px; padding: 54px 64px 64px; background: #1b1935;
 border: 1px solid #38345f; border-radius: 10px; box-shadow: 0 12px 35px #0006; }}
.page-label {{ position: absolute; top: 18px; right: 22px; color: #f472b6; font-size: 12px;
 font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }}
h1, h2, h3, h4 {{ color: #f9a8d4; line-height: 1.2; }} p, li {{ line-height: 1.62; }}
a {{ color: #22d3ee; }}
table {{ width: 100%; border-collapse: collapse; margin: 22px 0; font-size: 14px; }}
th, td {{ border: 1px solid #55517d; padding: 9px 11px; text-align: left; vertical-align: top; }}
th {{ background: #29264a; color: #f9a8d4; }} tr:nth-child(even) {{ background: #211f3e; }}
blockquote {{ margin-left: 0; padding-left: 18px; border-left: 3px solid #ec4899; color: #c9c7da; }}
code {{ background: #11121f; padding: .15em .35em; border-radius: 4px; }}
pre {{ overflow-x: auto; padding: 16px; background: #11121f; border-radius: 7px; }}
hr {{ border: 0; border-top: 1px solid #48446c; margin: 28px 0; }}
@media (max-width: 680px) {{ body {{ padding: 12px; }} .page {{ padding: 44px 22px 30px; }} }}
@media print {{ body {{ background: white; color: black; padding: 0; }} header {{ display: none; }}
 .page {{ color: black; background: white; border: 0; box-shadow: none;
  page-break-after: always; }} }}
</style></head><body><header><h1>{safe_title}</h1></header>{"".join(sections)}</body></html>"""
    return document.encode("utf-8")


def markdown_for_display(markdown: str) -> str:
    """Convert provider HTML tables and page markers to safe GFM for display.

    The provider's original Markdown remains unchanged for raw viewing and
    downloads. This function avoids enabling unsafe HTML in Streamlit while
    still rendering common NaviDC table output as Markdown tables.

    Args:
        markdown: Raw provider Markdown.

    Returns:
        Display-only GitHub Flavored Markdown without raw table elements.
    """

    def replace_table(match: re.Match[str]) -> str:
        parser = _TableParser()
        parser.feed(match.group(0))
        parser.close()
        return parser.as_markdown()

    rendered = _HTML_TABLE_PATTERN.sub(replace_table, markdown)
    rendered = _PAGE_MARKER_PATTERN.sub(r"\n\n---\n\n#### Page \1\n", rendered)
    return rendered.strip()


class _TableParser(HTMLParser):
    """Parse a provider HTML table into a small row-and-cell representation."""

    # Colspans are handled by padding empty cells so that the rendered
    # Markdown table has uniform column widths across all rows.
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None
        self._colspan = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell_parts = []
            attributes = dict(attrs)
            try:
                self._colspan = max(1, int(attributes.get("colspan", "1") or "1"))
            except ValueError:
                self._colspan = 1
        elif tag == "br" and self._cell_parts is not None:
            self._cell_parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._row is not None and self._cell_parts is not None:
            cell = _markdown_table_cell("".join(self._cell_parts))
            self._row.append(cell)
            self._row.extend([""] * (self._colspan - 1))
            self._cell_parts = None
            self._colspan = 1
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def as_markdown(self) -> str:
        """Render parsed rows as a rectangular GFM table."""
        if not self.rows:
            return ""
        column_count = max(len(row) for row in self.rows)
        rows = [row + [""] * (column_count - len(row)) for row in self.rows]
        header = rows[0]
        separator = ["---"] * column_count
        lines = [_markdown_row(header), _markdown_row(separator)]
        lines.extend(_markdown_row(row) for row in rows[1:])
        return "\n\n" + "\n".join(lines) + "\n\n"


def _markdown_table_cell(value: str) -> str:
    return " ".join(value.split()).replace("|", r"\|")


def _markdown_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _positive_float(values: Any, index: int) -> float:
    try:
        value = float(values[index])
        return value if value > 0 else 1.0
    except (IndexError, TypeError, ValueError):
        return 1.0


def _block_overlay(block: Any, page_width: float, page_height: float) -> str:
    # Not called anywhere in this repository. Converts layout bbox coordinates
    # to percentage-based CSS positioning relative to page_width and page_height
    # for rendering text region overlays.
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
