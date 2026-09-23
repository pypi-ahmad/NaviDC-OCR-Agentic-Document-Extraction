# Graph report: NaviDC-OCR-Agentic-Document-Extraction (2026-09-23)

## Corpus Check
- The corpus is about 29,594 words and fits in a single context window. A graph may be unnecessary for some questions.

## Summary
- 348 nodes · 679 edges · 23 communities (18 shown, 5 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Grounding and Evidence
- Schema Compilation
- Document Quality
- Provider Runtime
- Document Inputs
- Project Documentation
- OCR Knowledge Base
- OCR Design Decisions
- ADE Research
- OCR Inference Engine
- Streamlit Application
- HTML and Tests
- Artifact Bundles
- Table Parsing
- HTML Artifacts
- API Extraction
- ADE Knowledge Manifest
- Markdown Display
- Package Boundary
- Documentation Sync
- ADE Constraints
- Project Identity
- ADE Research Report

## God Nodes (most connected - your core abstractions)
1. `run_structured_extraction()` - 17 edges
2. `process_document()` - 16 edges
3. `SchemaDefinition` - 14 edges
4. `Technical documentation index` - 14 edges
5. `SchemaError` - 11 edges
6. `schema_definition()` - 11 edges
7. `SemanticError` - 11 edges
8. `NaviDC-OCR Document Extraction Studio README` - 11 edges
9. `compile_field_rows()` - 10 edges
10. `validate_record()` - 10 edges

## Potentially related nodes
- `Agentic document extraction domain and architecture` --semantically_similar_to--> `Architecture`  [INFERRED] [semantically similar]
  knowledge-base/landingai-ade/chunks/01-domain-and-architecture.md → docs/architecture.md
- `ADE security privacy retention and deployment` --semantically_similar_to--> `Security guidance`  [INFERRED] [semantically similar]
  knowledge-base/landingai-ade/chunks/05-security-privacy-deployment.md → SECURITY.md
- `ADE asynchronous jobs errors and operations` --semantically_similar_to--> `Operations runbook`  [INFERRED] [semantically similar]
  knowledge-base/landingai-ade/chunks/03-async-errors-operations.md → docs/operations-runbook.md
- `ADE capabilities schemas and grounding` --semantically_similar_to--> `Grounded structured extraction`  [INFERRED] [semantically similar]
  knowledge-base/landingai-ade/chunks/02-capabilities-schemas-grounding.md → README.md
- `make_bundle()` --uses--> `BundleInput`  [INFERRED]
  streamlit_app.py → src/agentic_document_extraction/artifacts.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Local document extraction workflow** — readme_document, docs_tutorial_first_extraction_document, docs_operations_runbook_document, docs_provider_api_document, docs_configuration_and_artifacts_document [INFERRED]
- **Documentation governance and validation** — contributing_document, docs_documentation_coverage_document, aiwg_reports_doc_sync_20260830_010640_document, docs_developer_guide_document [INFERRED]
- **Schema-grounded extraction and review** — readme_grounded_structured_extraction_concept, knowledge_base_landingai_ade_chunks_02_capabilities_schemas_grounding_concept, docs_configuration_and_artifacts_document [INFERRED]
- **Common adapter comparison for managed ADE and local NaviDC-OCR** — concept_ade_managed_document_extraction, concept_navidc_local_document_parsing, concept_navidc_worker_adapter [INFERRED 0.85]
- **NaviDC-OCR evidence-preserving pipeline** — knowledge_base_navidc_ocr_chunks_03_inference_pipeline_navidc_ocr_inference_pipeline, knowledge_base_navidc_ocr_chunks_04_inputs_outputs_navidc_ocr_inputs_and_outputs, concept_middle_json_as_evidence [INFERRED 0.85]
- **ADE release reproducibility controls** — concept_pinned_model_snapshot, concept_frozen_regression_corpus, concept_preview_features_deployment_gate [EXTRACTED 1.00]

## Communities (23 total, 5 thin omitted)

### Community 0 - "Grounding and Evidence"
Cohesion: 0.10
Nodes (42): collections_abc, decimal, difflib, jsonschema, openai, _bbox(), build_evidence_blocks(), _collect_block_text() (+34 more)

### Community 1 - "Schema Compilation"
Cohesion: 0.11
Nodes (32): copy, SchemaDefinition, compile_field_rows(), _csv_values(), extraction_response_schema(), _insert_field(), Any, ValueError (+24 more)

### Community 2 - "Document Quality"
Cohesion: 0.10
Nodes (28): cv2, ndarray, numpy, PageQuality, PreparedDocument, Any, QualityReport, Per-page scan-quality signals produced by quality.analyze_page(). dpi is the… (+20 more)

### Community 3 - "Provider Runtime"
Cohesion: 0.08
Nodes (27): dataclasses, httpx, os, Popen, NaviDcProvider, OcrProvider, ProviderError, ProviderOutput (+19 more)

### Community 4 - "Document Inputs"
Cohesion: 0.11
Nodes (26): hashlib, parametrize, pathlib, pil, re, DocumentError, DocumentInfo, _image_to_pdf() (+18 more)

### Community 5 - "Project Documentation"
Cohesion: 0.12
Nodes (26): Contributing guide, ADR-001 Isolated OCR worker, Architecture, Serialized GPU extraction, Configuration and artifact reference, Reproducible artifact bundle, Developer guide, Documentation coverage report (+18 more)

### Community 6 - "OCR Knowledge Base"
Cohesion: 0.12
Nodes (16): chunks, collection, counts, chunks, primary_sources, reference_notes, research_reports, depth (+8 more)

### Community 7 - "OCR Design Decisions"
Cohesion: 0.21
Nodes (15): Deterministic domain-schema mapping, Middle JSON as source evidence, NaviDC-OCR worker adapter, trust_remote_code supply-chain risk, NaviDC-OCR purpose and model, NaviDC-OCR data engine and training, NaviDC-OCR inference pipeline, NaviDC-OCR inputs and outputs (+7 more)

### Community 8 - "ADE Research"
Cohesion: 0.19
Nodes (14): ADE managed document extraction, Frozen regression corpus, NaviDC-OCR local document parsing, Pinned dated model snapshot, Preview features as deployment gate, Vendor benchmark not independently reproduced, ADE pricing, evaluation, and NaviDC-OCR fit, ADE versioning and release operations (+6 more)

### Community 9 - "OCR Inference Engine"
Cohesion: 0.15
Nodes (12): asyncio, fastapi, fastapi_responses, get, naviocr_config, naviocr_engine, naviocr_src_vlm_analyze, naviocr_src_vlm_middle_json_mkcontent (+4 more)

### Community 10 - "Streamlit Application"
Cohesion: 0.27
Nodes (12): cache_resource, streamlit, downloads(), ExtractionResult, json_bytes(), make_bundle(), ocr_provider(), process_document() (+4 more)

### Community 11 - "HTML and Tests"
Cohesion: 0.20
Nodes (10): datetime, io, json, pymupdf, pytest, build_html(), Convert extracted Markdown into a safe, standalone document view. Page markers…, test_build_html_escapes_unsafe_provider_html() (+2 more)

### Community 12 - "Artifact Bundles"
Cohesion: 0.24
Nodes (11): artifact_names(), build_bundle(), build_manifest(), BundleInput, Package extraction artifacts, metadata, and images into a ZIP archive. Args:…, Inputs required to create the final extraction bundle. Attributes:…, Derive all user-facing artifact names from a source filename. Args:…, Build serializable provenance metadata for an extraction. Args: item: Complete… (+3 more)

### Community 13 - "Table Parsing"
Cohesion: 0.18
Nodes (6): _markdown_row(), _markdown_table_cell(), HTMLParser, Parse a provider HTML table into a small row-and-cell representation., Render parsed rows as a rectangular GFM table., _TableParser

### Community 14 - "HTML Artifacts"
Cohesion: 0.31
Nodes (8): html, html_parser, markdown_it, _block_overlay(), _collect_text(), _positive_float(), Any, Artifact packaging and display conversion: standalone HTML, markdown, and ZIP…

### Community 15 - "API Extraction"
Cohesion: 0.29
Nodes (6): post, extract(), Response, Run OCR for an uploaded page-selected PDF. Args: document: Multipart PDF…, _run_extraction(), UploadFile

### Community 16 - "ADE Knowledge Manifest"
Cohesion: 0.33
Nodes (5): chunks, format, research_date, sources_file, title

### Community 17 - "Markdown Display"
Cohesion: 0.50
Nodes (4): markdown_for_display(), replace_table(), Convert provider HTML tables and page markers to safe GFM for display. The…, test_markdown_for_display_converts_html_tables_without_unsafe_html()

## Knowledge Gaps
- **33 isolated node(s):** `format`, `title`, `research_date`, `chunks`, `sources_file` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 133 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested graph queries
_Suggested queries based on graph structure:_

- **Why does `process_document()` connect `Streamlit Application` to `Grounding and Evidence`, `Schema Compilation`, `Document Quality`, `Document Inputs`, `HTML and Tests`, `Artifact Bundles`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `_TableParser` connect `Table Parsing` to `Markdown Display`, `HTML Artifacts`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `NaviDcProvider` connect `Provider Runtime` to `Streamlit Application`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `process_document()` (e.g. with `DocumentInfo` and `SchemaDefinition`) actually correct?**
  _`process_document()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `SchemaDefinition` (e.g. with `apply_manual_review()` and `generate_schema_from_guide()`) actually correct?**
  _`SchemaDefinition` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `SchemaError` (e.g. with `schema_controls()` and `test_schema_rejects_unsupported_keywords()`) actually correct?**
  _`SchemaError` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `format`, `title`, `research_date` to the rest of the system?**
  _33 weakly-connected nodes found - possible documentation gaps or missing edges._
