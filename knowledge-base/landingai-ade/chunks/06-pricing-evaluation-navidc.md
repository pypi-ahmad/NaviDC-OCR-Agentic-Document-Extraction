---
title: ADE pricing, evaluation, and NaviDC-OCR fit
source_urls: [https://docs.landing.ai/ade/ade-pricing, https://docs.landing.ai/ade/ade-credit-consumption, https://github.com/caipeng328/NaviDC-OCR]
research_date: 2026-08-29
---

# ADE pricing, evaluation, and NaviDC-OCR fit

Pricing on 2026-08-29: credits cost $0.01 on Explore/Team; Explore has 1,000 free credits; Team starts at $250/month. v1 Parse is 3 credits/page plus 1/page for ZDR. v1 Extract charges 1/5,000 input characters plus 1/1,000 output characters. Recheck v2 rates separately.

LandingAI reports 99.16% on DocVQA. This vendor claim was not reproduced and does not establish field, table, or grounding accuracy. Measure text/order, tables, per-field precision/recall, nulls, evidence, business-rule pass rate, latency, cost, and reviewer corrections.

ADE supplies managed APIs, extraction, evidence, jobs, billing, regions, and enterprise controls. NaviDC is local and emits Markdown, middle JSON, images, and layout PDF but lacks built-in schema extraction and managed operations. Compare both behind one adapter on a frozen representative corpus. Do not run both universally without measured gain.
