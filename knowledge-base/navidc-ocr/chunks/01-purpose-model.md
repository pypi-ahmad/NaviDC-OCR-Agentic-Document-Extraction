---
chunk_id: navidc-ocr-purpose-model
topics: [purpose, architecture, model]
evidence: verified
source_urls: [https://arxiv.org/abs/2608.12898v2, https://huggingface.co/StarDoc-AI/NaviDC-OCR/blob/c21590c42881b75965e5345530b01e9084fe7a6e/config.json]
---

# Purpose and model

NaviDC-OCR is a roughly 1.2B-parameter VLM for unified parsing of digital and camera-captured documents. The paper describes a Qwen2.5-VL-derived vision encoder, Qwen3-0.6B language model, and MLP aligner. Released BF16 checkpoint metadata counts 1,415,072,768 parameters. It is a decoupled parser: first layout, then content crops.

