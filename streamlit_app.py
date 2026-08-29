from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from typing import Any

import streamlit as st

from agentic_document_extraction.artifacts import (
    BundleInput,
    artifact_names,
    build_bundle,
    build_html,
    markdown_for_display,
)
from agentic_document_extraction.documents import (
    DocumentError,
    DocumentInfo,
    inspect_document,
    select_pdf_pages,
)
from agentic_document_extraction.models import QualityReport, SchemaDefinition, StructuredExtraction
from agentic_document_extraction.provider import NaviDcProvider, ProviderError, ProviderOutput
from agentic_document_extraction.quality import AccuracyMode, prepare_document, recommend_layout
from agentic_document_extraction.schemas import (
    SCHEMA_TEMPLATES,
    SchemaError,
    compile_field_rows,
    schema_definition,
    schema_to_field_rows,
    template_schema,
)
from agentic_document_extraction.semantic import (
    OpenAISemanticProvider,
    SemanticError,
    apply_manual_review,
    generate_schema_from_guide,
    run_structured_extraction,
)
from agentic_document_extraction.validation import objective

st.set_page_config(
    page_title="Document extraction studio",
    page_icon=":material/document_scanner:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    key: str
    markdown: str
    annotated_pdf: bytes
    html: bytes
    bundle: bytes
    names: dict[str, str]
    output: ProviderOutput
    quality: QualityReport
    definition: SchemaDefinition | None
    structured: StructuredExtraction | None
    selected_pdf: bytes
    layout_mode: str
    semantic_error: str = ""


@st.cache_resource
def ocr_provider() -> NaviDcProvider:
    return NaviDcProvider()


@st.cache_resource
def semantic_provider() -> OpenAISemanticProvider:
    return OpenAISemanticProvider()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def make_bundle(result: ExtractionResult, document: DocumentInfo, start: int, end: int) -> bytes:
    structured = result.structured
    return build_bundle(
        BundleInput(
            source_filename=document.filename,
            source_type=document.source_type,
            source_sha256=document.sha256,
            total_source_pages=document.total_pages,
            start_page=start,
            end_page=end,
            provider=result.output.provider,
            provider_model=result.output.model,
            layout_mode=result.layout_mode,
            accuracy_policy=result.quality.policy,
            markdown=result.output.markdown,
            annotated_pdf=result.annotated_pdf,
            html=result.html,
            images=result.output.images,
            structured_json=json_bytes(structured.as_dict()) if structured else None,
            schema_json=json_bytes(result.definition.schema) if result.definition else None,
            quality_json=json_bytes(result.quality.as_dict()),
            review_json=json_bytes([asdict(event) for event in structured.audit])
            if structured
            else None,
            field_guide=result.definition.field_guide.encode()
            if result.definition and result.definition.field_guide
            else None,
            semantic_model=structured.model if structured else None,
            reasoning_effort=structured.reasoning_effort if structured else None,
            schema_hash=result.definition.schema_hash if result.definition else None,
        )
    )


def process_document(
    document: DocumentInfo,
    start: int,
    end: int,
    requested_layout: str,
    accuracy: AccuracyMode,
    definition: SchemaDefinition | None,
) -> ExtractionResult:
    pages = list(range(start, end + 1))
    with st.status("Running agentic extraction…", expanded=True) as status:
        bar = st.progress(5, text="**5%** · Selecting pages")
        selected = select_pdf_pages(document.pdf_bytes, start, end)
        bar.progress(15, text="**15%** · Assessing and preparing scan quality")
        prepared = prepare_document(selected, pages, accuracy)
        layout = (
            recommend_layout(prepared.quality) if requested_layout == "Auto" else requested_layout
        )
        bar.progress(28, text=f"**28%** · Prepared at {prepared.quality.render_dpi} DPI · {layout}")
        ocr_provider().ensure_running()
        bar.progress(38, text="**38%** · Reading layout and text with NaviDC-OCR")
        output = ocr_provider().extract(
            prepared.pdf_bytes, pages, layout, prepared.quality.render_dpi
        )
        markdown = output.markdown.decode("utf-8", errors="replace")
        structured = None
        semantic_error = ""
        if definition:
            bar.progress(68, text="**68%** · Extracting, grounding, and validating fields")
            try:
                structured = run_structured_extraction(
                    semantic_provider(), markdown, output.middle_json, pages, definition
                )
                if accuracy == "Maximum" and structured.review_required:
                    bar.progress(78, text="**78%** · Comparing alternate layout strategy")
                    alternate = "Segmentation" if layout == "Detection" else "Detection"
                    alt_output = ocr_provider().extract(
                        prepared.pdf_bytes, pages, alternate, prepared.quality.render_dpi
                    )
                    alt_markdown = alt_output.markdown.decode("utf-8", errors="replace")
                    alt_structured = run_structured_extraction(
                        semantic_provider(), alt_markdown, alt_output.middle_json, pages, definition
                    )
                    if objective(alt_structured.fields, alt_structured.issues) > objective(
                        structured.fields, structured.issues
                    ):
                        output, markdown, structured, layout = (
                            alt_output,
                            alt_markdown,
                            alt_structured,
                            alternate,
                        )
            except SemanticError as exc:
                semantic_error = str(exc)
        else:
            bar.progress(78, text="**78%** · OCR complete · schema extraction skipped")
        bar.progress(90, text="**90%** · Building portable artifacts")
        html = build_html(markdown, f"{document.filename} · pages {start}–{end}")
        result = ExtractionResult(
            key=(
                f"{document.sha256}:{start}:{end}:{requested_layout}:{accuracy}:"
                f"{definition.schema_hash if definition else 'ocr-only'}"
            ),
            markdown=markdown,
            annotated_pdf=output.annotated_pdf,
            html=html,
            bundle=b"",
            names=artifact_names(document.filename),
            output=output,
            quality=prepared.quality,
            definition=definition,
            structured=structured,
            selected_pdf=selected,
            layout_mode=layout,
            semantic_error=semantic_error,
        )
        result = replace(result, bundle=make_bundle(result, document, start, end))
        bar.progress(100, text="**100%** · Extraction ready")
        status.update(label="Extraction complete", state="complete", expanded=False)
        return result


def schema_controls() -> SchemaDefinition | None:
    enabled = st.checkbox(
        "Add structured extraction",
        value=False,
        help="Optional: define fields, grounding, validation, and review after OCR.",
        key="structured_extraction_enabled",
    )
    if not enabled:
        st.caption("OCR, Markdown, annotated PDF, HTML, and ZIP remain available.")
        return None
    if "schema_rows" not in st.session_state:
        st.session_state.schema_rows = schema_to_field_rows(template_schema("Generic form"))
    st.caption("Extraction schema")
    template = st.selectbox("Template", list(SCHEMA_TEMPLATES))
    if st.button("Load template", width="stretch"):
        st.session_state.schema_rows = schema_to_field_rows(template_schema(template))
        st.session_state.pop("confirmed_schema", None)
        st.rerun()
    guide = st.file_uploader("Optional Markdown field guide", type=["md"])
    if guide and st.button("Generate schema draft", width="stretch"):
        try:
            text = guide.getvalue().decode()
            draft = generate_schema_from_guide(semantic_provider(), text, guide.name)
            st.session_state.schema_rows = schema_to_field_rows(draft.schema)
            st.session_state.generated_guide = text
            st.session_state.pop("confirmed_schema", None)
            st.rerun()
        except (UnicodeDecodeError, SchemaError, SemanticError) as exc:
            st.error(str(exc))
    rows = st.data_editor(
        st.session_state.schema_rows,
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "type": st.column_config.SelectboxColumn(
                "Type", options=["string", "number", "integer", "boolean"]
            ),
            "required": st.column_config.CheckboxColumn("Required"),
        },
        key="schema_editor",
    )
    with st.expander("Advanced JSON schema"):
        try:
            default_json = json.dumps(
                compile_field_rows(st.session_state.schema_rows, template), indent=2
            )
        except SchemaError:
            default_json = "{}"
        advanced = st.text_area("JSON schema", default_json, height=220)
        use_advanced = st.checkbox("Use advanced JSON instead of builder")
    if st.button("Confirm schema", width="stretch"):
        try:
            schema = json.loads(advanced) if use_advanced else compile_field_rows(rows, template)
            st.session_state.confirmed_schema = schema_definition(
                template, schema, st.session_state.get("generated_guide", "")
            )
        except (json.JSONDecodeError, SchemaError) as exc:
            st.error(str(exc))
    definition = st.session_state.get("confirmed_schema")
    st.caption(
        f"Confirmed · {definition.schema_hash[:10]}…"
        if definition
        else "Confirm the schema to enable structured extraction."
    )
    return definition


def downloads(result: ExtractionResult) -> None:
    st.sidebar.subheader("Downloads")
    st.sidebar.download_button(
        "Complete bundle",
        result.bundle,
        result.names["bundle"],
        "application/zip",
        type="primary",
        width="stretch",
        on_click="ignore",
    )
    for label, data, key, mime in (
        ("Markdown", result.markdown, "markdown", "text/markdown"),
        ("Annotated PDF", result.annotated_pdf, "annotated_pdf", "application/pdf"),
        ("HTML", result.html, "html", "text/html"),
    ):
        st.sidebar.download_button(
            label, data, result.names[key], mime, width="stretch", on_click="ignore"
        )
    if result.structured:
        st.sidebar.download_button(
            "Structured JSON",
            json_bytes(result.structured.as_dict()),
            "extraction.json",
            "application/json",
            width="stretch",
            on_click="ignore",
        )


st.title("Document extraction studio")
st.caption("Local NaviDC-OCR · grounded schema extraction · confidence-led review")
with st.sidebar:
    st.header("Source")
    upload = st.file_uploader(
        "Upload a document", type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"], max_upload_size=100
    )

document = None
if upload:
    try:
        document = inspect_document(upload.name, upload.getvalue(), upload.type)
    except DocumentError as exc:
        st.error(str(exc))
if document is None:
    with st.container(border=True):
        st.subheader("Start with a scan")
        st.write("Upload a PDF or image. Uploaded content remains session-scoped on this machine.")
    st.stop()

with st.sidebar:
    st.caption(document.filename)
    c1, c2 = st.columns(2)
    c1.metric("Pages", document.total_pages)
    c2.metric("Size", f"{document.size_bytes / 1024 / 1024:.1f} MB")
    if document.source_type == "pdf":
        p1, p2 = st.columns(2)
        start = int(p1.number_input("Start", 1, document.total_pages, 1))
        end = int(p2.number_input("End", 1, document.total_pages, document.total_pages))
    else:
        start = end = 1
    st.subheader("Accuracy")
    accuracy = st.select_slider("Policy", ["Fast", "Balanced", "Maximum"], value="Maximum")
    layout = (
        st.segmented_control("Layout", ["Auto", "Detection", "Segmentation"], default="Auto")
        or "Auto"
    )
    st.caption(f"Pages {start}–{end} · {end - start + 1} selected")
    st.subheader("Optional enrichment")
    definition = schema_controls()
    extract = st.button(
        "Extract document",
        type="primary",
        width="stretch",
        disabled=start > end,
    )

selected_pdf = select_pdf_pages(document.pdf_bytes, start, end)
schema_hash = definition.schema_hash if definition else "ocr-only"
current_key = f"{document.sha256}:{start}:{end}:{layout}:{accuracy}:{schema_hash}"
result: ExtractionResult | None = st.session_state.get("extraction_result")
if result and result.key != current_key:
    st.session_state.pop("extraction_result", None)
    result = None
if extract:
    try:
        result = process_document(document, start, end, layout, accuracy, definition)
        st.session_state.extraction_result = result
    except (DocumentError, ProviderError, SchemaError) as exc:
        st.error(str(exc))
    except Exception:
        st.error(
            "Extraction stopped unexpectedly. Review the launcher console and try fewer pages."
        )

if not result:
    st.subheader("Source preview")
    st.pdf(selected_pdf, height=780)
    st.stop()

downloads(result)
if result.semantic_error:
    st.warning(f"OCR succeeded, but structured extraction is unavailable: {result.semantic_error}")
summary, rendered, raw, review, pdf, html_tab, quality = st.tabs(
    ["Summary", "Rendered Markdown", "Raw Markdown", "Review", "Annotated PDF", "HTML", "Quality"]
)
with summary:
    if result.structured:
        a, b, c = st.columns(3)
        a.metric("Fields", len(result.structured.fields))
        b.metric("Issues", len(result.structured.issues))
        c.metric("Review", "Required" if result.structured.review_required else "Complete")
        st.json(result.structured.record)
    else:
        st.info("OCR artifacts are ready; structured extraction was not completed.")
with rendered:
    st.markdown(markdown_for_display(result.markdown))
with raw:
    st.code(result.markdown, language="markdown", line_numbers=True)
with review:
    if result.structured:
        rows = [
            {
                "field": f.field_path,
                "value": json.dumps(f.value, ensure_ascii=False),
                "confidence": round(f.verification_score * 100),
                "status": f.status,
                "page": f.evidence.page if f.evidence else None,
                "quote": f.evidence.quote if f.evidence else "",
            }
            for f in result.structured.fields
        ]
        st.dataframe(rows, hide_index=True, width="stretch")
        path = st.selectbox("Field", [row["field"] for row in rows])
        field = next(item for item in result.structured.fields if item.field_path == path)
        value_text = st.text_input("JSON value", json.dumps(field.value, ensure_ascii=False))
        action = (
            st.segmented_control("Decision", ["accept", "correct", "reject"], default="accept")
            or "accept"
        )
        if st.button("Apply review decision"):
            try:
                value = None if action == "reject" else json.loads(value_text)
                updated = apply_manual_review(
                    result.structured, path, value, action, result.definition
                )
                result = replace(result, structured=updated)
                result = replace(result, bundle=make_bundle(result, document, start, end))
                st.session_state.extraction_result = result
                st.rerun()
            except (json.JSONDecodeError, KeyError, IndexError) as exc:
                st.error(f"Enter a valid JSON value: {exc}")
    else:
        st.info("No fields are available for review.")
with pdf:
    st.pdf(result.annotated_pdf, height=780)
with html_tab:
    st.iframe(result.html.decode("utf-8"), height=780)
with quality:
    st.caption(f"{result.quality.policy} · {result.quality.render_dpi} DPI")
    st.dataframe([asdict(page) for page in result.quality.pages], width="stretch")
