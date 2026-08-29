---
title: NaviDC-OCR runtime and integration contract
source_urls:
  - https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/infer.py
  - https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/engine.py
  - https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/vlm_utils/NaviOCR_client.py
source_type: primary
retrieved: 2026-08-29
---

# Runtime and integration contract

CLI input is a directory. Each supported image or PDF is converted to PDF bytes, rasterized, layout-parsed, crop-parsed, and assembled. Sync and async entry points are `do_parse` and `aio_do_parse`.

The VLM receives distinct prompts for layout, text, OTSL tables, LaTeX formulas, code, scientific-figure tables, table structure, and formula structure. Layout is first predicted from a normalized page; region crops then receive their matching prompt.

Default files written per document are Markdown, middle JSON, a layout-annotated PDF, and extracted images. In-memory return data is middle JSON.

Integration inference: place this behind a narrow worker/service adapter. Avoid coupling UI code to upstream globals, filesystem layout, or backend-specific objects. Preserve middle JSON as evidence and perform domain schema validation outside the model.

