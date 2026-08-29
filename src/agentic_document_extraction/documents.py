from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


class DocumentError(ValueError):
    """Raised when an uploaded document cannot be processed safely."""


class PageRangeError(DocumentError):
    """Raised when a requested page range is invalid."""


@dataclass(frozen=True, slots=True)
class DocumentInfo:
    """Validated document metadata and its normalized PDF representation.

    Attributes:
        filename: Original base filename supplied by the uploader.
        stem: Filesystem-safe stem used for generated artifact names.
        source_type: Normalized input type such as ``pdf`` or ``jpg``.
        mime_type: Resolved MIME type for the uploaded source.
        size_bytes: Size of the original upload.
        total_pages: Number of pages in the source; images always have one.
        pdf_bytes: Original PDF or image normalized as a one-page PDF.
        sha256: SHA-256 digest of the original uploaded bytes.
    """

    filename: str
    stem: str
    source_type: str
    mime_type: str
    size_bytes: int
    total_pages: int
    pdf_bytes: bytes
    sha256: str


def safe_stem(filename: str) -> str:
    """Create a bounded, filesystem-safe artifact stem.

    Args:
        filename: User-supplied source filename.

    Returns:
        A non-empty ASCII stem containing only letters, numbers, dots,
        underscores, and hyphens, limited to 80 characters.
    """
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).stem).strip("-._")
    return stem[:80] or "document"


def validate_page_range(start_page: int, end_page: int, total_pages: int) -> tuple[int, int]:
    """Validate a one-based inclusive page range.

    Args:
        start_page: First source page to process.
        end_page: Last source page to process.
        total_pages: Number of pages in the source document.

    Returns:
        The validated ``(start_page, end_page)`` pair.

    Raises:
        PageRangeError: If the document is empty or the range is outside it,
            empty, or reversed.
    """
    if total_pages < 1 or not (1 <= start_page <= end_page <= total_pages):
        raise PageRangeError(
            f"Choose pages within 1–{max(total_pages, 1)}, with the start before the end."
        )
    return start_page, end_page


def select_pdf_pages(pdf_bytes: bytes, start_page: int, end_page: int) -> bytes:
    """Copy an inclusive page range into a new PDF in source order.

    Args:
        pdf_bytes: Source PDF content.
        start_page: One-based first page to copy.
        end_page: One-based last page to copy.

    Returns:
        Bytes for a new PDF containing only the selected pages.

    Raises:
        DocumentError: If the source cannot be opened.
        PageRangeError: If the requested range is invalid.
    """
    try:
        source = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise DocumentError("The PDF could not be opened.") from exc
    try:
        validate_page_range(start_page, end_page, source.page_count)
        selected = pymupdf.open()
        selected.insert_pdf(source, from_page=start_page - 1, to_page=end_page - 1)
        result = selected.tobytes(garbage=4, deflate=True)
        selected.close()
        return result
    finally:
        source.close()


def inspect_document(filename: str, data: bytes, mime_type: str | None = None) -> DocumentInfo:
    """Validate an upload and normalize it for the OCR pipeline.

    PDF uploads retain their original bytes. Supported images are flattened
    onto a white background and converted to a one-page PDF. Only the first
    TIFF frame is used.

    Args:
        filename: Uploaded filename, including its extension.
        data: Uploaded file bytes.
        mime_type: Optional uploader-provided MIME type.

    Returns:
        Validated metadata and normalized PDF bytes.

    Raises:
        DocumentError: If the upload is empty, oversized, unsupported,
            password-protected, damaged, or unreadable.
    """
    if not data:
        raise DocumentError("The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentError("The uploaded file exceeds the 100 MB limit.")
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentError("Upload a PDF, PNG, JPG, JPEG, TIF, or TIFF file.")

    if extension == ".pdf":
        normalized, total_pages = _inspect_pdf(data)
        source_type = "pdf"
        resolved_mime = "application/pdf"
    else:
        normalized = _image_to_pdf(data)
        total_pages = 1
        source_type = extension.removeprefix(".").replace("jpeg", "jpg").replace("tiff", "tif")
        resolved_mime = (
            mime_type
            or {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".tif": "image/tiff",
                ".tiff": "image/tiff",
            }[extension]
        )

    return DocumentInfo(
        filename=Path(filename).name,
        stem=safe_stem(filename),
        source_type=source_type,
        mime_type=resolved_mime,
        size_bytes=len(data),
        total_pages=total_pages,
        pdf_bytes=normalized,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _inspect_pdf(data: bytes) -> tuple[bytes, int]:
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
        if document.needs_pass:
            raise DocumentError("Password-protected PDFs are not supported.")
        if document.page_count < 1:
            raise DocumentError("The PDF contains no pages.")
        page_count = document.page_count
        document.close()
        return data, page_count
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("The PDF is damaged or unreadable.") from exc


def _image_to_pdf(data: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.seek(0)
            image.load()
            normalized = ImageOps.exif_transpose(image).convert("RGBA")
            canvas = Image.new("RGB", normalized.size, "white")
            canvas.paste(normalized, mask=normalized.getchannel("A"))
            output = io.BytesIO()
            canvas.save(output, format="PDF", resolution=150)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise DocumentError("The image is damaged or unreadable.") from exc


def render_pdf_pages(pdf_bytes: bytes, scale: float = 1.35) -> list[bytes]:
    """Rasterize every PDF page as a JPEG image.

    Args:
        pdf_bytes: PDF content to render.
        scale: PyMuPDF render scale applied in both dimensions.

    Returns:
        JPEG bytes in PDF page order.

    Raises:
        RuntimeError: If PyMuPDF cannot open or render the PDF.
    """
    document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        matrix = pymupdf.Matrix(scale, scale)
        return [
            page.get_pixmap(matrix=matrix, alpha=False).tobytes("jpeg", jpg_quality=86)
            for page in document
        ]
    finally:
        document.close()
