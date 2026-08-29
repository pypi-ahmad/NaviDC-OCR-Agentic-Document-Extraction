# Knowledge Base: Agentic Document Extraction and LandingAI ADE

Research date and cutoff: 2026-08-29

## Summary

Reference and RAG-ready knowledge grounded in first-party LandingAI documentation and source repositories. Vendor benchmark and compliance statements remain vendor claims unless independently verified.

## Topics

- [Domain and architecture](chunks/01-domain-and-architecture.md)
- [ADE capabilities, schemas, and grounding](chunks/02-capabilities-schemas-grounding.md)
- [Async jobs, errors, and operations](chunks/03-async-errors-operations.md)
- [Formats, languages, and limits](chunks/04-formats-languages-limits.md)
- [Security, privacy, and deployment](chunks/05-security-privacy-deployment.md)
- [Pricing, evaluation, and NaviDC fit](chunks/06-pricing-evaluation-navidc.md)
- [Versioning and release operations](chunks/07-versioning-and-release-operations.md)

## Sources

- [Deep research synthesis](../../research/AGENTIC-DOCUMENT-EXTRACTION-LANDINGAI-ADE-DEEP-RESEARCH.md)
- [Official ADE documentation](sources/official-ade-docs.md)
- [Official Python SDK](sources/ade-python-sdk.md)
- [NaviDC-OCR local research](sources/navidc-local.md)
- [Source manifest](sources.json)
- [RAG manifest](manifest.json)

## Usage notes

Retrieve the smallest relevant chunk. Verify pricing, limits, security attestations, and API-generation details against current official pages before consequential use. Treat marked inference as design guidance.

## Rerun inputs

```yaml
workflow: firecrawl-knowledge-base
source: https://docs.landing.ai/ade, https://github.com/landing-ai/ade-python
goal: reference-and-rag
depth: thorough
output_dir: knowledge-base/landingai-ade
raw_dir: .firecrawl
research_date: 2026-08-29
```
