---
title: ADE versioning and release operations
source_urls: [https://docs.landing.ai/ade/ade-changelog, https://docs.landing.ai/ade/ade-parse-models, https://docs.landing.ai/ade/ade-extract-models]
research_date: 2026-08-29
---

# ADE versioning and release operations

LandingAI's official changelog shows that ADE is a moving service contract. In April 2026, the `dpt-2` and `dpt-2-latest` aliases moved to a new parsing snapshot, and LandingAI warned that results may change. Pin a dated model snapshot for reproducible production output; use a `-latest` alias only when automatic behavior changes are acceptable.

The April 2026 Extract release added cross-page table reconstruction, support for documents of 1,000 or more pages, removal of documented schema-length and nesting limits, and a Build Extract Schema API. These are vendor-documented capabilities, not locally reproduced performance or accuracy results.

Extract Jobs became available in June 2026 for long documents and complex schemas. Persist job IDs, poll with bounded backoff, and record the model version, SDK version, schema version, and response metadata with every result.

Classify and Section entered public preview in April 2026. The official changelog says preview features may be inaccurate and should not be used in production. Treat preview status as a deployment gate, not merely a documentation label.

Enterprise IP allowlisting, released in August 2026, applies to v1 and v2 API requests but not to the Playground. Organizations using the Playground need a separate access-control assessment.

Operational recommendation: maintain a frozen regression corpus and run it before changing any model alias, SDK, extraction schema, prompt, or API generation. Compare field accuracy, null behavior, table structure, grounding, partial failures, latency, and credits before promotion.
