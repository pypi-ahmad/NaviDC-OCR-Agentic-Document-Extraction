from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime

import pymupdf
import pytest

from agentic_document_extraction.artifacts import BundleInput, build_bundle
from agentic_document_extraction.documents import (
    PageRangeError,
    select_pdf_pages,
    validate_page_range,
)


@pytest.mark.parametrize("start,end,total", [(1, 1, 1), (1, 4, 4), (2, 3, 4)])
def test_validate_page_range_accepts_inclusive_ranges(start: int, end: int, total: int) -> None:
    assert validate_page_range(start, end, total) == (start, end)


@pytest.mark.parametrize("start,end,total", [(0, 1, 2), (2, 1, 2), (1, 3, 2), (1, 1, 0)])
def test_validate_page_range_rejects_invalid_ranges(start: int, end: int, total: int) -> None:
    with pytest.raises(PageRangeError):
        validate_page_range(start, end, total)


def test_select_pdf_pages_preserves_inclusive_order() -> None:
    source = pymupdf.open()
    for page_number in range(1, 5):
        page = source.new_page()
        page.insert_text((72, 72), f"PAGE {page_number}")
    source_bytes = source.tobytes()
    source.close()

    selected = select_pdf_pages(source_bytes, 2, 3)
    document = pymupdf.open(stream=selected, filetype="pdf")

    assert document.page_count == 2
    assert [page.get_text().strip() for page in document] == ["PAGE 2", "PAGE 3"]
    document.close()


def test_build_bundle_contains_artifacts_assets_and_manifest() -> None:
    generated_at = datetime(2026, 8, 29, 12, 30, tzinfo=UTC)
    bundle = build_bundle(
        BundleInput(
            source_filename="invoice.pdf",
            source_type="pdf",
            source_sha256="abc123",
            total_source_pages=7,
            start_page=2,
            end_page=4,
            provider="NaviDC-OCR",
            provider_model="StarDoc-AI/NaviDC-OCR",
            layout_mode="Detection",
            markdown=b"# Invoice\n",
            annotated_pdf=b"annotated",
            html=b"<!doctype html>",
            images={"figure-1.png": b"image"},
            generated_at=generated_at,
        )
    )

    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        assert set(archive.namelist()) == {
            "invoice.md",
            "invoice_annotated.pdf",
            "invoice_view.html",
            "manifest.json",
            "images/figure-1.png",
        }
        manifest = json.loads(archive.read("manifest.json"))

    assert manifest["source_filename"] == "invoice.pdf"
    assert manifest["source_type"] == "pdf"
    assert manifest["selected_page_range"] == {"start": 2, "end": 4}
    assert manifest["total_source_page_count"] == 7
    assert manifest["ocr_provider"] == "NaviDC-OCR"
    assert manifest["generated_at"] == "2026-08-29T12:30:00+00:00"
    assert manifest["artifacts"] == {
        "markdown": "invoice.md",
        "annotated_pdf": "invoice_annotated.pdf",
        "html": "invoice_view.html",
    }
