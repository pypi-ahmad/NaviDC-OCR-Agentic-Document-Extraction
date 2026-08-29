---
title: ADE capabilities, schemas, and grounding
source_urls: [https://docs.landing.ai/ade/ade-overview, https://docs.landing.ai/ade/ade-extract-schema-json, https://github.com/landing-ai/ade-python]
research_date: 2026-08-29
---

# ADE capabilities, schemas, and grounding

Verified: ADE offers Parse, Extract, Classify, Section, and Split. Parse returns Markdown, elements, grounding, and metadata. Extract consumes Markdown and a schema. Classify labels pages independently. Section builds a table of contents. Split separates mixed documents. Section and Split are Preview in v1.

SDK v2 accepts Pydantic models, dictionaries, or JSON strings. v1 schema types include object, array, boolean, integer, number, and string. Missing primitives return `null`, arrays `[]`, and objects retain nullable children. Unsupported keywords can be normalized, ignored, or cause 206/422 depending on `strict`.

Parse ties elements to page boxes and Markdown ranges. Extract ties values to source ranges or chunk references. Grounding supports review but does not prove correctness. Current SDK guidance uses `client.v2` for DPT-3 Parse/Extract; direct client methods retain v1/DPT-2 operations.
