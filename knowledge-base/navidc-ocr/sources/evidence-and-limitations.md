---
title: NaviDC-OCR evidence and limitations
source_urls:
  - https://arxiv.org/abs/2608.12898v2
  - https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/README.md
  - https://github.com/caipeng328/NaviDC-OCR/tree/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616
source_type: primary
retrieved: 2026-08-29
---

# Evidence and limitations

Verified:

- Benchmark numbers are author-reported and evaluation-path dependent.
- No upstream tests or CI workflow exist at inspected revision.
- No dedicated limitations section appears in paper v2.
- Default runtime assumes high GPU allocation and vLLM async execution.
- CLI filters only JSON and HTML before attempting byte-based type detection.
- Top-level async CLI still processes documents one at a time.

Not established by primary sources:

- handwriting quality;
- production latency or throughput on named GPU hardware;
- practical CPU performance;
- robust support beyond the three model-card languages;
- deterministic domain-schema extraction;
- Windows-native deployment quality.

Secondary Firecrawl results were used only to discover the primary GitHub, arXiv, and Hugging Face pages. ResearchGate, Medium, Quora, LLM Explorer, and LlamaIndex results were excluded from factual synthesis.

