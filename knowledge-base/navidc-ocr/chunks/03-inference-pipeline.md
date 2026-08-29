---
chunk_id: navidc-ocr-inference-pipeline
topics: [inference, layout, extraction, post-processing]
evidence: verified
source_urls: [https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/vlm_utils/NaviOCR_client.py, https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/engine.py]
---

# Inference pipeline

Input bytes become PDF pages, then page images. A normalized page receives a layout prompt. Parsed regions are cropped from higher-resolution page data and sent with type-specific prompts for text, tables, formulas, code, or scientific figures. Post-processing converts OTSL tables to HTML, cleans LaTeX, orders content, and builds Markdown plus middle JSON.

