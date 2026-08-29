from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from agentic_document_extraction.artifacts import (
    BundleInput,
    artifact_names,
    build_bundle,
    build_original_style_html,
)
from agentic_document_extraction.documents import (
    DocumentError,
    DocumentInfo,
    inspect_document,
    select_pdf_pages,
)
from agentic_document_extraction.provider import NaviDcProvider, ProviderError, ProviderOutput

st.set_page_config(
    page_title="Document extraction studio",
    page_icon=":material/document_scanner:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Session-scoped artifacts prepared for preview and download."""

    key: str
    markdown: str
    annotated_pdf: bytes
    html: bytes
    bundle: bytes
    names: dict[str, str]


@st.cache_resource
def provider() -> NaviDcProvider:
    """Return the process-wide cached NaviDC provider adapter."""
    return NaviDcProvider()


def process_document(
    document: DocumentInfo, start_page: int, end_page: int, layout_mode: str
) -> ExtractionResult:
    """Run OCR and build all user-facing artifacts for a selected range.

    Args:
        document: Validated source document.
        start_page: One-based first selected source page.
        end_page: One-based last selected source page.
        layout_mode: NaviDC layout strategy.

    Returns:
        Artifacts and stable input key for Streamlit session state.

    Raises:
        DocumentError: If page selection fails.
        ProviderError: If the local OCR service cannot complete extraction.
    """
    with st.status("Preparing document…", expanded=True) as status:
        progress = st.progress(10, text="Selecting source pages")
        selected_pdf = select_pdf_pages(document.pdf_bytes, start_page, end_page)
        source_pages = list(range(start_page, end_page + 1))

        progress.progress(25, text="Starting local NaviDC-OCR service")
        provider().ensure_running()

        progress.progress(40, text="Reading layout and content with NaviDC-OCR")
        output: ProviderOutput = provider().extract(selected_pdf, source_pages, layout_mode)

        progress.progress(80, text="Building HTML and download bundle")
        html_bytes = build_original_style_html(
            selected_pdf,
            output.middle_json,
            source_pages,
            f"{document.filename} · pages {start_page}–{end_page}",
        )
        bundle_input = BundleInput(
            source_filename=document.filename,
            source_type=document.source_type,
            source_sha256=document.sha256,
            total_source_pages=document.total_pages,
            start_page=start_page,
            end_page=end_page,
            provider=output.provider,
            provider_model=output.model,
            layout_mode=layout_mode,
            markdown=output.markdown,
            annotated_pdf=output.annotated_pdf,
            html=html_bytes,
            images=output.images,
        )
        names = artifact_names(document.filename)
        result = ExtractionResult(
            key=f"{document.sha256}:{start_page}:{end_page}:{layout_mode}",
            markdown=output.markdown.decode("utf-8", errors="replace"),
            annotated_pdf=output.annotated_pdf,
            html=html_bytes,
            bundle=build_bundle(bundle_input),
            names=names,
        )
        progress.progress(100, text="Artifacts ready")
        status.update(label="Extraction complete", state="complete", expanded=False)
        return result


def show_downloads(result: ExtractionResult) -> None:
    """Render sidebar download buttons for a completed extraction.

    Args:
        result: Session-scoped extraction artifacts and filenames.
    """
    st.sidebar.subheader("Downloads")
    st.sidebar.download_button(
        "Download bundle",
        result.bundle,
        result.names["bundle"],
        "application/zip",
        icon=":material/folder_zip:",
        type="primary",
        width="stretch",
        on_click="ignore",
    )
    st.sidebar.download_button(
        "Markdown",
        result.markdown,
        result.names["markdown"],
        "text/markdown",
        icon=":material/markdown:",
        width="stretch",
        on_click="ignore",
    )
    st.sidebar.download_button(
        "Annotated PDF",
        result.annotated_pdf,
        result.names["annotated_pdf"],
        "application/pdf",
        icon=":material/picture_as_pdf:",
        width="stretch",
        on_click="ignore",
    )
    st.sidebar.download_button(
        "Original-style HTML",
        result.html,
        result.names["html"],
        "text/html",
        icon=":material/html:",
        width="stretch",
        on_click="ignore",
    )


st.title("Document extraction studio")
st.caption("Private, local extraction with NaviDC-OCR · Markdown, annotations, and visual HTML")

with st.sidebar:
    st.header("Source")
    upload = st.file_uploader(
        "Upload a document",
        type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
        max_upload_size=100,
        help="PDF, PNG, JPEG, or TIFF up to 100 MB.",
    )

document: DocumentInfo | None = None
if upload is not None:
    try:
        document = inspect_document(upload.name, upload.getvalue(), upload.type)
    except DocumentError as exc:
        st.error(str(exc), icon=":material/error:")

if document is None:
    with st.container(border=True):
        st.subheader("Start with a scan")
        st.write(
            "Upload a PDF or image. Your file stays on this machine and is not retained by the app."
        )
        st.caption(
            "NaviDC-OCR preserves reading order, tables, fields, and layout where available."
        )
    st.stop()

with st.sidebar:
    st.caption(document.filename)
    meta_col1, meta_col2 = st.columns(2)
    meta_col1.metric("Pages", document.total_pages)
    meta_col2.metric("Size", f"{document.size_bytes / 1024 / 1024:.1f} MB")
    st.caption(f"{document.source_type.upper()} · SHA-256 {document.sha256[:10]}…")

    if document.source_type == "pdf":
        st.subheader("Pages")
        range_col1, range_col2 = st.columns(2)
        start_page = int(range_col1.number_input("Start", 1, document.total_pages, 1, step=1))
        end_page = int(
            range_col2.number_input("End", 1, document.total_pages, document.total_pages, step=1)
        )
    else:
        start_page = end_page = 1
        st.caption("Images are processed as page 1.")

    st.subheader("OCR")
    layout_mode = (
        st.segmented_control(
            "Layout mode",
            ["Detection", "Segmentation"],
            default="Detection",
            help="Detection is the reliable default. Segmentation can help dense page layouts.",
        )
        or "Detection"
    )
    selected_count = end_page - start_page + 1
    if selected_count > 25:
        st.warning(
            "Large ranges take longer and may exhaust 8 GB GPU memory. Smaller batches are safer."
        )
    st.caption(f"Selected: pages {start_page}–{end_page} · {selected_count} page(s)")
    extract_clicked = st.button(
        "Extract document",
        type="primary",
        icon=":material/document_scanner:",
        width="stretch",
        disabled=start_page > end_page,
    )

selected_pdf = (
    select_pdf_pages(document.pdf_bytes, start_page, end_page)
    if start_page <= end_page
    else document.pdf_bytes
)
current_key = f"{document.sha256}:{start_page}:{end_page}:{layout_mode}"
stored_result: ExtractionResult | None = st.session_state.get("extraction_result")
if stored_result is not None and stored_result.key != current_key:
    del st.session_state["extraction_result"]
    stored_result = None

if extract_clicked:
    try:
        stored_result = process_document(document, start_page, end_page, layout_mode)
        st.session_state["extraction_result"] = stored_result
    except (DocumentError, ProviderError) as exc:
        st.error(str(exc), icon=":material/error:")
    except Exception:
        st.error(
            "Extraction stopped unexpectedly. Check the local runtime "
            "and try a smaller page range.",
            icon=":material/error:",
        )

if stored_result is not None:
    show_downloads(stored_result)
    rendered_tab, raw_tab, pdf_tab, html_tab = st.tabs(
        ["Rendered Markdown", "Raw Markdown", "Annotated PDF", "Original-style HTML"]
    )
    with rendered_tab:
        st.markdown(stored_result.markdown)
    with raw_tab:
        st.code(stored_result.markdown, language="markdown", line_numbers=True)
    with pdf_tab:
        st.pdf(stored_result.annotated_pdf, height=780)
    with html_tab:
        st.iframe(stored_result.html.decode("utf-8"), height=780, scrolling=True)
else:
    st.subheader("Source preview")
    st.caption(f"Pages {start_page}–{end_page} of {document.total_pages}")
    st.pdf(selected_pdf, height=780)
