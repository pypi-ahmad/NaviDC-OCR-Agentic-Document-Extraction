# Agentic Document Extraction and LandingAI ADE: deep research

**Research and access date:** 2026-08-29  
**Evidence policy:** **Verified** = supported by a cited primary source. **Vendor claim** = LandingAI's claim, not independently reproduced here. **Recommendation** = implementation guidance derived from the evidence. **Unknown** = not disclosed or not found in the reviewed primary sources.

## Executive conclusion

Agentic document extraction is best understood as a document-processing system, not an OCR feature. OCR recognizes glyphs. A modern parser also reconstructs reading order, layout, tables, figures, forms, and source coordinates. An extraction system maps that representation to typed business fields. An *agentic* system adds goal-directed routing and bounded iteration: it can choose a parser or schema, inspect evidence, retry a failed stage, invoke validation, and escalate uncertain cases. No reviewed standards body defines this term; that broader definition is an analytical model, while “Agentic Document Extraction” is also LandingAI's product name.[^ade-overview]

LandingAI ADE exposes five functional APIs: Parse, Extract, Classify, Section, and Split. Most documented workflows begin with Parse; Classify can operate directly on the original document; Extract, Section, and Split consume parsed content.[^ade-overview] The production-safe interpretation is a deterministic workflow around probabilistic components: policy controls ingestion and routing permissions, models do perception and semantic mapping, deterministic validators enforce contracts, and humans resolve consequential ambiguity.

A crucial integration finding is that LandingAI currently has two documentation generations. The established ADE/v1 documentation and current Python examples describe DPT-2 parsing and `extract-latest`; LandingAI's July 2026 “2nd Generation” announcement says the platform is moving to DPT-3. Legacy documentation explicitly deprecates the original combined endpoint, DPT-1, `dpt-2-mini`, and the old `agentic-doc` library.[^gen2][^legacy][^python] **Recommendation:** pin the exact API generation, endpoint region, SDK version, parsing model snapshot, extraction model, and schema revision in every stored result. Do not infer DPT-3 request or response contracts from DPT-2 examples.

## 1. Capability model and reference architecture

| Layer | Purpose | Typical output | Main failure class |
| --- | --- | --- | --- |
| File normalization | Decode or convert PDF, image, Office, or spreadsheet input | normalized pages | conversion/layout drift |
| OCR / visual recognition | recognize visible symbols | text spans and boxes | substitutions, omissions |
| Layout parsing | recover document structure and reading order | Markdown, chunks, tables, hierarchy | wrong order or grouping |
| Semantic extraction | map evidence to a schema | typed fields and arrays | hallucination, wrong association |
| Classification/splitting | identify page/document type and boundaries | labels and subdocuments | boundary or class error |
| Validation | enforce syntax and business rules | accepted record or violations | incomplete rules |
| Workflow/agent layer | choose actions, retry, route, escalate | decision trace and terminal state | loops, unsafe autonomy, cost amplification |

LandingAI defines a chunk as a discrete document element and says ADE performs semantic rather than fixed-length chunking. Chunks contain content plus location data; documented types extend beyond text/table/figure to forms, marginalia, cards, barcodes, QR codes, logos, and attestations depending on model support.[^chunks][^models]

**Recommended production flow**

1. Accept a document only after MIME verification, malware scanning, tenant authorization, and size/page checks.
2. Store the immutable input hash and policy decision.
3. Optionally Classify pages when routing before parsing is valuable.
4. Parse once into Markdown, chunks, grounding, splits, and processing metadata.
5. If the input is a bundle, Split the parsed representation using explicit type and instance rules.
6. Select a versioned extraction schema by trusted routing logic, not instructions found inside the document.
7. Extract fields and preserve per-field evidence.
8. Validate types, cross-field invariants, totals, dates, identifiers, and required evidence.
9. Retry only a classified, recoverable failure with a bounded budget; otherwise send to review.
10. Persist the record, evidence, model/schema versions, warnings, latency, credits, and decision trace.

This architecture is a **recommendation**, not LandingAI's disclosed internal agent graph. LandingAI does not publish its internal prompts, orchestration, model training corpus, or retry policy.

## 2. LandingAI ADE workflow surface

### Parse

**Verified:** Parse accepts either a file (`document`) or URL (`document_url`) and returns structured Markdown, chunks, and metadata with page/coordinate references.[^parse] The Python library exposes `response.markdown`, `response.chunks`, `response.metadata`, `response.splits`, and `response.grounding`; chunk grounding includes a zero-indexed page and a box with left/top/right/bottom coordinates.[^python]

Document Pre-Trained Transformer (DPT) is LandingAI's parsing model family. Its documented role is to detect layout and chunks and generate captions for chunks.[^models] DPT-2 snapshots are frozen dated versions, while `dpt-2` and `dpt-2-latest` follow the newest snapshot. LandingAI warns that a moving alias can change results; a dated snapshot preserves behavior.[^models]

The Parse `split` parameter is not the Split API. The former controls organization of the parse response; the latter separates a parsed bundle into classified subdocuments.[^parse]

### Extract and schemas

**Verified:** Extract operates on parsed Markdown plus a schema and returns `extraction`, `extraction_metadata`, and processing `metadata`.[^extract][^extract-response] The Python SDK accepts a Pydantic model, Python dictionary, or JSON string for the schema and uses `model="extract-latest"` in current examples.[^python]

The v1 schema surface documents object, array, boolean, integer, number, and string types; descriptions, enums, formats, array items, object properties, and `x-alternativeNames` guide extraction.[^schema] Missing primitives are represented as `null`, arrays as `[]`, while object shapes are retained with nullable children.[^schema] Some unsupported JSON Schema keywords can be ignored, normalized, or rejected depending on strictness, so “valid JSON Schema” is not sufficient evidence that ADE implements every keyword.[^schema]

`extraction_metadata` maps extracted fields to source chunks. Metadata can also report credit use, duration, version, validation errors, and a fallback model version when a requested extraction model was not used.[^extract-response][^changelog]

**Recommendation:** make every field description operational: define meaning, units, allowed normalization, null policy, whether inference is forbidden, and how to distinguish similar candidates. Keep schemas narrow and version them. Validate the response independently; a schema-guided model is not a database constraint.

### Classify

**Verified:** Classify receives the original document plus caller-defined classes and assigns a class to each page. It can run before or without Parse and can guide page routing, splitting, or schema selection.[^classify] SDK results contain a zero-indexed page, predicted class, and may return `unknown` plus a suggested class.[^python]

**Important status:** the official page marks Classify **Preview**, says it may be inaccurate, and says not to use it in production.[^classify]

### Split

**Verified:** Split runs after Parse and before optional Extract. It consumes parsed Markdown and rules containing a required `name`, optional description, and optional unique-instance `identifier`; it returns classification, identifier, page membership, and subdocument Markdown.[^split][^python]

**Important status:** Split is **Preview** and the official page explicitly says not to use it in production.[^split] A production bundle separator therefore needs either an accepted-risk exception, deterministic/manual verification, or another supported mechanism.

### Section

**Verified:** Section consumes reference-anchored Parse Markdown and returns a reading-order table of contents with hierarchy levels and the chunk reference where each section starts.[^section][^changelog] This is useful for navigation and retrieval boundaries, but hierarchy correctness must be evaluated separately from OCR accuracy.

### Synchronous and asynchronous work

The SDK exposes synchronous methods and Parse/Extract jobs. Jobs return an ID, expose pending/processing/completed/failed/cancelled lifecycle states, and are polled for results.[^parse-jobs][^extract-jobs][^python] A Parse job may complete while some pages failed; callers must inspect HTTP 206 and `failed_pages`/`failure_reason`, not treat `completed` as fully successful.[^changelog][^parse-response]

**Recommendation:** use jobs for long or complex work, implement idempotency in the application, store job IDs, use exponential backoff with jitter, and cap both retries and total credit spend. No contracted webhook mechanism was found in reviewed official sources.

## 3. Response and provenance contract

A robust adapter should normalize ADE responses to this application-owned contract:

```json
{
  "document_hash": "sha256:...",
  "parser": {"provider": "landingai", "api_generation": "v1", "model": "dpt-2-20260410"},
  "content": {"markdown": "...", "chunks": [], "grounding": {}, "splits": []},
  "extraction": {"schema_id": "invoice@3", "record": {}, "evidence": {}},
  "quality": {"failed_pages": [], "validation_errors": [], "review_required": false},
  "operations": {"job_id": "...", "duration_ms": 0, "credits": 0},
  "audit": {"received_at": "...", "policy_version": "..."}
}
```

This is a **recommendation**. It insulates downstream systems from provider response changes and ensures provenance is not discarded.

Grounding is evidence, not certainty. DPT-2 documentation describes chunk and table-cell confidence from 0 to 1 and low-confidence character spans; the changelog notes table-cell row/column positions.[^changelog][^parse-response] **Recommendation:** render the cited crop beside the normalized field during review and test whether the cited location actually supports the value. A plausible value with an unrelated box is a grounding failure.

## 4. Inputs, languages, and operational limits

**Verified input types:** PDF; JPEG/JPG/PNG/WEBP plus numerous API-only image formats; DOC/DOCX/ODT; PPT/PPTX; CSV; XLSX.[^files] Office documents are converted to PDF and may undergo layout changes. Playground spreadsheets are limited to 10 MB and API/library spreadsheets to 50 MB. XLSX processing documents limits and omission behavior for very large sheets.[^files]

The public v1 documentation lists strong support for English, Simplified and Traditional Chinese, Dutch, French, German, Italian, Japanese, Korean, Portuguese, Russian, and Spanish, with additional languages at moderate or basic support.[^languages] **Recommendation:** interpret these as vendor support tiers, not accuracy guarantees; test the exact script, scan quality, and domain vocabulary.

Limits are endpoint- and generation-specific. Current SDK text describes Parse Jobs up to 1 GB and, in one section, 1,000 pages; the changelog states the job limit was subsequently raised to 6,000 pages.[^python][^changelog] Synchronous Parse is documented at 100 pages.[^files][^limits] Classify troubleshooting states a 200 MB size ceiling.[^classify-troubleshoot] **Recommendation:** query the live endpoint documentation during implementation and encode limits per operation rather than a single global constant.

## 5. DPT-2, DPT-3, and version boundaries

### Verified DPT-2 facts

- DPT-2 is documented as recognizing complex/no-gridline/merged-cell tables, expanded chunk types, and improved layout detection; these are vendor capability claims, not reproduced results.[^models]
- Dated snapshots can be pinned; aliases move.[^models]
- The April 2026 documented snapshot is `dpt-2-20260410`; omission or `dpt-2-latest` selected the current DPT-2 snapshot on the reviewed v1 page.[^models]
- Confidence and detailed table-cell grounding were added to DPT-2 responses.[^changelog]

### DPT-3 / “2nd Generation”

**Vendor claim:** LandingAI announced in July 2026 that ADE would be powered by a DPT-3 family designed for documents, with more agent-friendly output, more detailed citations, higher performance, and improved cost efficiency.[^gen2] The separate v2 credit page confirms that v2 has its own billing rules.[^v2-credits]

**Unknown:** the reviewed official search did not expose a complete stable DPT-3 API schema, full output contract, supported language matrix, reproducible benchmark protocol, or migration compatibility guarantee. Therefore, this report does not project v1/DPT-2 fields onto v2/DPT-3.

## 6. Conventional OCR versus agentic extraction

| Dimension | Conventional OCR | Agentic document extraction |
| --- | --- | --- |
| Primary goal | transcribe visible text | produce task-specific structured records |
| Context | local glyph/line context | page, document, schema, and workflow context |
| Layout | optional boxes/lines | reading order, semantic chunks, hierarchy, tables |
| Output | text/spans | Markdown/tree + typed record + evidence |
| Control flow | usually fixed pipeline | conditional routing, bounded retries, escalation |
| Evaluation | CER/WER | parsing + field + grounding + workflow metrics |
| Main new risk | recognition error | plausible unsupported fields, unsafe routing, loops/cost |

Agentic extraction does not eliminate OCR-style error. It layers additional semantic decisions on top, creating both value and new failure modes. **Recommendation:** retain deterministic controls at trust boundaries. Document text is untrusted input; it must not alter system prompts, call arbitrary tools, choose a tenant, bypass review, or expand permissions.

## 7. Evaluation plan

LandingAI reports 5,286 correct answers out of 5,331 on the DocVQA validation split (99.16%), using an LLM that answered from ADE's parsed response without image access during QA. The company attributes only 18 of 45 wrong answers to parsing.[^docvqa] This is a useful first-party experiment but not a complete extraction evaluation: it evaluates question answering over a known benchmark and was not independently reproduced here.

**Recommended metrics**

| Stage | Metrics |
| --- | --- |
| OCR/text | character and word error rate; normalized exact match |
| Reading order | pairwise/order accuracy; heading hierarchy accuracy |
| Tables | cell precision/recall, row/column alignment, merged-cell fidelity, cross-page reconstruction |
| Extraction | per-field exact/normalized match, precision/recall/F1, null accuracy, array cardinality |
| Grounding | cited-value support rate, box IoU where truth exists, wrong-source rate |
| Classification/split | per-class F1, unknown rate, boundary F1, instance purity |
| Workflow | straight-through rate, review rate, retry rate, terminal failure rate |
| Operations | p50/p95/p99 latency, credits/document, duplicate cost, partial-page rate |
| Safety | prompt-injection compliance, tenant isolation, unauthorized action rate |

Build a frozen, versioned golden corpus stratified by source: born-digital PDF, clean scan, skew/noise, camera photo, handwriting, multi-column, long/cross-page tables, mixed bundles, Office conversions, spreadsheets, each required language, and adversarial document text. Maintain separate development and blind acceptance sets. Report confidence intervals and cohort results; a global average hides costly failure pockets.

For every model or schema change, run paired regression tests. Block rollout on high-risk-field regressions even if the overall score rises. Shadow new versions, sample evidence visually, and retain a rollback path to the pinned snapshot.

## 8. Production reliability and failure controls

| Failure | Detection | Control |
| --- | --- | --- |
| Unsupported/corrupt input | 4xx and decode error | quarantine; controlled conversion |
| Partial Parse | 206, `failed_pages` | reject completeness-sensitive jobs or reprocess pages |
| Layout drift after Office conversion | visual/golden diff | request PDF or verify converted render |
| Wrong class/boundary | class/boundary benchmark | manual/deterministic check; Preview restriction |
| Wrong but plausible value | evidence and business rule failure | source rendering plus human review |
| Missing field | null/empty semantics | explicit required-field policy |
| Model alias drift | recorded model differs | pin snapshot and gated upgrade |
| Extraction fallback | `fallback_model_version` | log, alert, evaluate fallback separately |
| Timeout/retry duplication | duplicate job/hash/cost | idempotency registry and bounded retry |
| Schema overload | latency/errors/field regression | smaller domain schemas, async jobs |
| Prompt injection in document | unsafe requested action | treat content as data; fixed tool allowlist |

The SDK is generated from the API specification and supports Python and TypeScript. Python installation is `landingai-ade`; authentication uses `VISION_AGENT_API_KEY`, and the client can target the EU environment.[^python][^typescript] **Recommendation:** keep the key in the runtime secret store, never document contents or logs; rotate it, scope network egress, and separate keys by environment and region.

## 9. Security, privacy, and deployment

LandingAI documents US hosting in AWS Ohio and EU hosting in Ireland, with region-specific keys; EU documentation states data is processed and stored in the EU.[^eu] Enterprise offerings list VPC and on-premises options.[^pricing]

LandingAI lists SOC 2 Type II, GDPR, and HIPAA-related controls. HIPAA use requires a signed BAA and Zero Data Retention (ZDR).[^security][^zdr] ZDR documentation says documents/intermediates are deleted after processing, results are deleted upon delivery/fetch, and ZDR content is not used to train or improve models; unfetched v2 async results are deleted within a stated 24–48 hour window.[^zdr] Treat these as vendor contractual/operational claims and verify scope, subprocessors, evidence, and current terms through procurement and the Trust Center.

Enterprise IP allowlisting applies to v1 and v2 API requests across API keys but does not restrict the Playground.[^ip-allowlist][^changelog] **Recommendation:** disable or govern Playground use for sensitive production data; an API allowlist alone is not a complete exfiltration control.

Security checklist:

- classify data and select region/deployment before upload;
- establish DPA/BAA and verify ZDR semantics for synchronous and asynchronous flows;
- encrypt inputs, outputs, evidence, and backups; restrict evidence crops as sensitive data;
- isolate tenants in storage, queues, caches, logs, review UI, and keys;
- log document hashes and metadata, not raw document content by default;
- validate remote URLs to prevent SSRF and disallow private/link-local targets;
- scan archives and converted documents; cap decompression, pixels, pages, and runtime;
- prohibit document-originated instructions from invoking tools or changing policy;
- define deletion, legal hold, incident response, and audit-evidence procedures.

## 10. Practical integration blueprint

### Narrow proof of value

1. Select one document family and 20–100 representative files.
2. Define a small schema and field-level ground truth, including null cases.
3. Run Parse and inspect Markdown, tables, reading order, chunks, and grounding.
4. Run Extract; score fields and cited evidence separately.
5. Record latency and credits by page/type.
6. Enumerate failure cohorts and decide which require review.

### Production adapter

- Expose provider-neutral `parse`, `extract`, `classify`, and `split` interfaces.
- Preserve raw provider responses in restricted storage while returning a stable internal model.
- Record provider, region, endpoint generation, SDK, requested/actual model, schema, policy, and prompt/rule versions.
- Detect 206 and semantic incompleteness; never equate HTTP 200 with accepted business output.
- Use a state machine with explicit terminal outcomes: accepted, review, rejected, failed.
- Implement budgets for pages, retries, elapsed time, and credits.
- Make writes downstream idempotent and require review for irreversible/high-impact actions.

### RAG-specific guidance

Index semantic chunks with document ID, page, box, type, heading path, and model version. Keep the original Markdown and coordinates so retrieved passages can be rendered as citations. Avoid re-chunking tables blindly by token count. Evaluate retrieval recall and citation support, not only answer fluency.

## 11. Pricing and capacity

LandingAI prices Explore and Team credits at $0.01 each, with Enterprise custom pricing; every API and Playground run consumes credits.[^pricing] v1 and v2 have separate consumption schedules, so cost models must be generation-specific.[^pricing][^v2-credits] Organization limits aggregate across keys and depend on plan/operation.[^limits]

**Recommendation:** calculate cost per accepted document—not merely per page—because retries, partial results, schema extraction, split/classify calls, and human review change unit economics. Alert on credit velocity and cap automatic retries.

## 12. Decision guidance

Use ADE when managed parsing, schema extraction, grounding, long-document jobs, regional SaaS, and a short integration path outweigh vendor dependency and usage cost. Prefer a local or VPC/on-prem path when policy forbids third-party processing, offline operation is required, or workload economics and engineering capacity favor self-hosting. A hybrid adapter is often sensible: route allowed documents to ADE, regulated or offline cohorts locally, then apply the same validation and evaluation contract.

Do not deploy Classify or Split as an unattended production dependency while their official pages retain the Preview/no-production warning.[^classify][^split] Do not adopt DPT-3 based only on marketing performance claims: obtain the current v2 contract, run the golden corpus, validate security/retention, measure cost, and define rollback.

## 13. Verified gaps and source limitations

- No standards-based definition of “agentic document extraction” was found.
- LandingAI's internal agent architecture, prompts, training data, and model-routing logic are not public.
- No independent reproduction of LandingAI's DocVQA result was performed.
- The public DPT-3 search surface was materially thinner than the v1/DPT-2 documentation; exact v2 contracts must be confirmed before implementation.
- No official webhook contract or built-in human-review queue was found in the reviewed sources.
- Trust Center audit reports and contractual documents were not accessed.
- No documents were uploaded and no paid ADE calls were made; capability and latency were not empirically tested.

## Reproduction and knowledge-base record

Firecrawl searches with scraped content were saved under `.firecrawl/`, including:

- `.firecrawl/search-landing-ade-dpt3-official.json`
- `.firecrawl/search-landing-ade-workflows-official.json`
- `.firecrawl/search-agentic-document-extraction-primary.json`
- `.firecrawl/search-landing-dpt3-platform.json`

All four were verified non-empty and received one substantive feedback event. Only official LandingAI documentation, first-party LandingAI posts, and official SDK documentation were used for factual product claims. This Markdown file is the curated reference layer; the JSON files retain the collected source content for future reprocessing.

## Sources

All sources accessed 2026-08-29.

[^ade-overview]: LandingAI, [Agentic Document Extraction overview](https://docs.landing.ai/ade/ade-overview).
[^parse]: LandingAI, [Parse Documents](https://docs.landing.ai/ade/parse).
[^parse-response]: LandingAI, [JSON Response for Parsing](https://docs.landing.ai/ade/ade-json-response).
[^chunks]: LandingAI, [Chunk Types](https://docs.landing.ai/ade/ade-chunk-types).
[^models]: LandingAI, [Document Pre-Trained Transformers (Parsing Models)](https://docs.landing.ai/ade/ade-parse-models).
[^extract]: LandingAI, [Extract](https://docs.landing.ai/ade/ade-extract).
[^extract-response]: LandingAI, [JSON Response for Extraction](https://docs.landing.ai/ade/ade-extract-response).
[^schema]: LandingAI, [Extraction Schema](https://docs.landing.ai/ade/ade-extract-schema-json).
[^classify]: LandingAI, [Classify](https://docs.landing.ai/ade/ade-classify).
[^classify-troubleshoot]: LandingAI, [Troubleshoot Classification](https://docs.landing.ai/ade/ade-classify-troubleshoot).
[^split]: LandingAI, [Split](https://docs.landing.ai/ade/ade-split).
[^section]: LandingAI, [Section](https://docs.landing.ai/ade/ade-section).
[^parse-jobs]: LandingAI, [Asynchronous Parsing](https://docs.landing.ai/ade/ade-parse-async).
[^extract-jobs]: LandingAI, [Asynchronous Extraction](https://docs.landing.ai/ade/ade-extract-async).
[^files]: LandingAI, [Supported File Types](https://docs.landing.ai/ade/ade-file-types).
[^languages]: LandingAI, [Supported Languages](https://docs.landing.ai/ade/ade-languages).
[^limits]: LandingAI, [Rate Limits](https://docs.landing.ai/ade/ade-rate-limits).
[^python]: LandingAI, [Python Library](https://docs.landing.ai/ade/ade-python) and [`landing-ai/ade-python`](https://github.com/landing-ai/ade-python).
[^typescript]: LandingAI, [TypeScript Library](https://docs.landing.ai/ade/ade-typescript) and [`landing-ai/ade-typescript`](https://github.com/landing-ai/ade-typescript).
[^legacy]: LandingAI, [Legacy ADE Features](https://docs.landing.ai/ade/ade-overview-legacy).
[^changelog]: LandingAI, [ADE Changelog](https://docs.landing.ai/ade/ade-changelog).
[^gen2]: LandingAI, [Introducing Agentic Document Extraction, 2nd Generation](https://landing.ai/blog/introducing-agentic-document-extraction-gen2), 2026-07-20.
[^docvqa]: LandingAI, [DocVQA Benchmark: 99.16% Accuracy Using Agentic Document Extraction](https://landing.ai/blog/docvqa-benchmark), 2025-11-12.
[^pricing]: LandingAI, [Plans & Billing](https://docs.landing.ai/ade/ade-pricing).
[^v2-credits]: LandingAI, [Credit Consumption for ADE v2](https://docs.landing.ai/dpt3/credit-consumption).
[^security]: LandingAI, [Security](https://docs.landing.ai/ade/ade-security).
[^zdr]: LandingAI, [Zero Data Retention](https://docs.landing.ai/ade/zdr).
[^eu]: LandingAI, [European Union](https://docs.landing.ai/ade/ade-eu).
[^ip-allowlist]: LandingAI, [IP Address Allowlist](https://docs.landing.ai/ade/ip-allowlist).
