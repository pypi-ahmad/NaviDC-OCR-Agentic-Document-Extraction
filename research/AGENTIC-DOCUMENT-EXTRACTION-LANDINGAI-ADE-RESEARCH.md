# Agentic document extraction and LandingAI ADE research

Research date and knowledge cutoff: 2026-08-29  
Evidence labels: **Verified** means a primary source supports the statement. **Vendor claim** means LandingAI reports it but this work did not reproduce it. **Inference** is system-design analysis, not disclosed architecture.

## Executive summary

Agentic document extraction is not a synonym for OCR. OCR recognizes text; parsing reconstructs elements, reading order, tables, figures, and geometry; extraction maps that representation to a requested schema. An agentic workflow adds context-sensitive routing, tool choice, iterative correction, evidence gathering, and stop or escalation rules. **Inference:** production systems should keep ingestion, policy, validation, provenance, and acceptance deterministic while limiting model discretion to ambiguous work.

LandingAI Agentic Document Extraction (ADE) is a managed document-intelligence platform with Parse, Extract, Classify, Section, and Split APIs. Its current Python SDK exposes `client.v2` for DPT-3 parsing and extraction plus asynchronous jobs. Live v1 documentation covers DPT-2 and the broader Classify, Section, Split, and schema-building surface. Integrations must pin a generation instead of mixing examples.[^overview][^sdk]

ADE is broader than NaviDC-OCR: managed APIs, schema extraction, field evidence, jobs, billing, regional SaaS, and enterprise controls. NaviDC is a local parser producing Markdown and intermediate JSON without managed extraction or operations. A hybrid can use local parsing plus a separate extraction and validation layer. ADE is shorter when SaaS use and credit pricing are acceptable.[^navidc]

## Boundaries and reference architecture

| Layer | Responsibility | Output |
| --- | --- | --- |
| OCR | Recognize glyphs | text spans, sometimes boxes |
| Parsing | Recover layout and structure | Markdown/HTML, element tree, coordinates |
| IDP | Classify, route, extract, validate, integrate | typed records and workflow decisions |
| Agentic extraction | Select or iterate tools and checks against a goal | record, evidence, warnings, decision trace |

No inspected standard gives “agentic document extraction” a fixed definition. LandingAI uses it as a product name; this broader taxonomy is analysis.[^overview]

Reference flow:

1. Authenticate and enforce file, tenant, and retention policy.
2. Parse into ordered elements, Markdown, structure, and coordinates.
3. Choose schema, page subset, model tier, and fallback using explicit policy.
4. Extract fields, attach evidence, and validate schema and business rules.
5. Return record, evidence, warnings, versions, latency, and cost.

**Inference:** an agent must not silently replace contradictory evidence. Financial, medical, identity, and compliance errors that are hard to detect require human review or read-only downstream access.

## ADE capabilities

### Parse and Extract

**Verified:** Parse returns Markdown and structured JSON, with text, tables, images/figures, form fields, and barcodes described as chunks. Current SDK v2 returns a document/page/element tree with grounding and metadata including page count, failed pages, duration, and billing. Partial page failures can return HTTP 206.[^parse][^parse-json][^sdk]

Extract consumes Parse Markdown plus a schema and returns `extraction`, field-level `extraction_metadata`, and processing metadata. SDK schemas may be Pydantic models, dictionaries, or JSON strings. v1 supports object, array, boolean, integer, number, and string plus `description`, string `enum`, `format`, `items`, `properties`, and `x-alternativeNames`. Missing primitives return `null`, arrays `[]`, and objects retain nullable children. Unsupported keywords may be ignored, converted, or return 206/422 depending on keyword and `strict`.[^extract][^extract-json][^schema][^sdk]

The v1 guide states no maximum schema property count. This does not establish accuracy or latency for arbitrarily large schemas.[^schema]

### Grounding

**Verified:** Parse links elements to pages, boxes, and Markdown ranges. Extract metadata links values to source ranges or chunk references. Grounding enables review, but model-produced coordinates are not proof of correctness.[^parse-json][^extract-json][^grounding]

### Classify, Section, and Split

**Verified for v1:** Classify labels pages from caller-defined classes without Parse. Section creates a hierarchical table of contents. Split separates mixed parsed documents. Section and Split are Preview. These methods sit on the SDK v1 surface; the current v2 path centers on Parse and Extract.[^overview][^classify][^section][^sdk]

### Async and errors

Jobs expose create, get, list, and polling; current SDK v2 also provides `wait()` with backoff. States are `pending`, `processing`, `completed`, `failed`, and `cancelled`. Large results can use output URLs. No webhook/callback contract was found in official docs or SDK specs; use polling unless LandingAI documents a contracted alternative.[^async-parse][^async-extract][^sdk]

The SDK retries connection errors and HTTP 408, 409, 429, and 5xx twice by default. Default timeout is eight minutes. A synchronous 504 cancels that workflow; retry starts fresh work. HTTP success does not imply complete parsing because 206 can carry failed pages.[^sdk][^sdk-spec]

No built-in human-review queue was found. Applications needing review must implement assignment, correction, audit history, and acceptance thresholds.

## Inputs, languages, and limits

**Verified for v1:** supported inputs include PDF, many image formats, DOC/DOCX/ODT, PPT/PPTX, CSV, and XLSX. Office files are converted to PDF and layout may change. API spreadsheet limit is 50 MB. XLSX parsing covers up to 65,536 rows and columns; excess is omitted. Synchronous Parse accepts 100 PDF pages; Parse Jobs accept 1 GB or 6,000 pages.[^files][^limits]

Strong language support is listed for English, Simplified/Traditional Chinese, Dutch, French, German, Italian, Japanese, Korean, Portuguese, Russian, and Spanish; 14 languages have moderate support and several complex scripts basic support. DPT-3 Verity is Latin-script only. These are support statements, not reproduced tests.[^languages]

## SDK and integration contract

**Verified at inspected `ade-python` revision:** package version 1.17.1, Apache-2.0, Python 3.9+, sync/async clients, HTTPX, Pydantic models, configurable timeouts/retries, and `VISION_AGENT_API_KEY`. The generated specs contain compatibility routes across generations; prefer public SDK methods over hard-coded paths from a generated snapshot.[^sdk][^sdk-pyproject][^sdk-spec]

## Security, privacy, and deployment

Vendor documentation lists GDPR, SOC 2 Type II, and HIPAA-related controls. SAML/OIDC SSO and IP allowlists are Enterprise features. Verify certification scope and dates through the Trust Center. HIPAA use requires ZDR and a signed BAA.[^security][^zdr]

ZDR is Team/Enterprise. LandingAI states that it deletes documents and intermediates after processing, deletes results on delivery, and does not train or improve models with ZDR data. Unfetched v2 async results are deleted between 24 and 48 hours after completion; fetched results are deleted on fetch. v1 ZDR jobs require URL input and `output_save_url`.[^zdr]

Hosted regions are AWS Ohio (`us-east-2`) and Ireland (`eu-west-1`). The EU service states data is stored and processed in the EU; keys are region-specific. Enterprise lists VPC and on-prem deployments. Customers remain responsible for their VPC infrastructure and subprocessors.[^eu][^pricing][^zdr]

## Pricing and rate limits

**Verified on 2026-08-29; recheck before budgeting:** Explore and Team credits cost $0.01. Explore starts with 1,000 free credits, Team packs at $250/month, and Enterprise is custom. v1 Parse costs 3 credits/page plus 1/page for ZDR. v1 Extract costs 1 per 5,000 input characters plus 1 per 1,000 output characters, rounded up to 0.1. Classify costs 0.5/page; Section uses Extract's character factors; Split costs 1 per 5,000 input characters. Separate v2 rules exist, so v1 rates must not be applied to v2.[^pricing][^credits]

Limits depend on plan, are distributed per minute, and aggregate across an organization. Exact hourly values were absent from the inspected public page. Extract Jobs have a separate submission limit.[^limits]

## Accuracy and evaluation

**Vendor claim:** LandingAI reports 99.16% on DocVQA. This was not reproduced and does not measure table fidelity, schema-field precision/recall, grounding, or domain exception handling.[^overview]

Production evaluation should measure text and reading order, table cells, per-field exact/normalized match, null behavior, grounding correctness, business-rule pass rate, straight-through processing, latency, credits, partial results, retries, and human corrections. Freeze a golden set covering clean PDFs, scans, photos, long and mixed bundles, spreadsheets, relevant languages, and prompt-like adversarial text.

## Failure modes and controls

- Office conversion can alter layout.[^files]
- Malformed schemas can yield 206 partial content, 422, or keyword normalization.[^schema]
- Parse can return partial page failures.[^sdk]
- Sync timeout retries repeat work and cost; use bounded jobs for long inputs.[^sdk-spec]
- Grounding may cite the wrong region; render evidence for sampled or high-risk fields.
- Agent retries can amplify cost and inconsistency; bound attempts and preserve versions.
- Document text is untrusted data and must never expand permissions or override policy.

## ADE versus NaviDC-OCR

| Dimension | LandingAI ADE | NaviDC-OCR |
| --- | --- | --- |
| Delivery | Managed US/EU SaaS; Enterprise VPC/on-prem listed | Local CUDA-oriented pipeline |
| Output | Markdown, structure, grounding, metadata | Markdown, middle JSON, images, layout PDF |
| Schema extraction | Built in with field evidence | Not built in |
| Operations | Jobs, SDK retries, credits, regional keys | Host builds service, queue, limits, monitoring |
| Data control | Vendor controls; ZDR paid tiers | Local, subject to dependency/model trust |
| Cost | Credits | Hardware, engineering, operations |

**Inference:** define one adapter contract for both: document plus policy options in; Markdown, elements, evidence, warnings, versions, timing, and cost out. Compare on a frozen corpus. Do not run both on every page without measured benefit.[^navidc]

## Recommended sequence

1. Create 20 to 100 representative documents with field truth.
2. Build one narrow interface and ADE/NaviDC adapters preserving raw evidence.
3. Compare parsing, fields, grounding, latency, and cost by cohort.
4. Add deterministic validation and review for unresolved high-risk fields.
5. Add agentic routing only for measured failure classes with clear stop conditions.

## Unverified or unavailable

- Internal models, prompts, training mix, agent graph, and routing are unpublished.
- Production uptime, latency, field accuracy, and capacity need customer testing or contracts.
- No public webhook or first-party human-review queue was found.
- Trust Center reports were not accessed.
- Current v2 pricing and limits must be checked in DPT-3 docs; `/ade` mixes v1 pages and v2 links.

## Reproduction record

Three Firecrawl searches used `--scrape`, produced non-empty JSON under `.firecrawl/`, and received one substantive feedback event each. A docs map found 68 URLs; 20 primary pages were scraped. Official `ade-python` and `agentic-doc` repos were shallow-cloned under `.firecrawl/github.com/landing-ai/`. No API call, upload, dependency install, or paid evaluation ran.

## Sources

[^overview]: LandingAI, [ADE overview](https://docs.landing.ai/ade/ade-overview).
[^parse]: LandingAI, [Parse](https://docs.landing.ai/ade/parse).
[^parse-json]: LandingAI, [Parse JSON](https://docs.landing.ai/ade/ade-json-response).
[^extract]: LandingAI, [Extract](https://docs.landing.ai/ade/ade-extract).
[^extract-json]: LandingAI, [Extract JSON](https://docs.landing.ai/ade/ade-extract-response).
[^schema]: LandingAI, [Extraction Schema](https://docs.landing.ai/ade/ade-extract-schema-json).
[^grounding]: LandingAI, [Extraction grounding](https://docs.landing.ai/ade/ade-extract-grounding-sample).
[^classify]: LandingAI, [Classify](https://docs.landing.ai/ade/ade-classify).
[^section]: LandingAI, [Section](https://docs.landing.ai/ade/ade-section).
[^async-parse]: LandingAI, [Parse Jobs](https://docs.landing.ai/ade/ade-parse-async).
[^async-extract]: LandingAI, [Extract Jobs](https://docs.landing.ai/ade/ade-extract-async).
[^files]: LandingAI, [File types](https://docs.landing.ai/ade/ade-file-types).
[^languages]: LandingAI, [Languages](https://docs.landing.ai/ade/ade-languages).
[^limits]: LandingAI, [Rate limits](https://docs.landing.ai/ade/ade-rate-limits).
[^security]: LandingAI, [Security](https://docs.landing.ai/ade/ade-security).
[^zdr]: LandingAI, [ZDR](https://docs.landing.ai/ade/zdr).
[^eu]: LandingAI, [EU deployment](https://docs.landing.ai/ade/ade-eu).
[^pricing]: LandingAI, [Plans and billing](https://docs.landing.ai/ade/ade-pricing).
[^credits]: LandingAI, [v1 credit consumption](https://docs.landing.ai/ade/ade-credit-consumption).
[^sdk]: LandingAI, [`ade-python` README](https://github.com/landing-ai/ade-python/blob/main/README.md), inspected 2026-08-29.
[^sdk-pyproject]: LandingAI, [`ade-python` metadata](https://github.com/landing-ai/ade-python/blob/main/pyproject.toml), version 1.17.1 inspected.
[^sdk-spec]: LandingAI, [`ade-python` generated specs](https://github.com/landing-ai/ade-python/tree/main/specs).
[^navidc]: [Local NaviDC-OCR research](NAVIDC-OCR-RESEARCH.md).
