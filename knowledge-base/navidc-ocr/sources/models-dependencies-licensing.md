---
title: NaviDC-OCR models, dependencies, and licensing
source_urls:
  - https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/pyproject.toml
  - https://huggingface.co/StarDoc-AI/NaviDC-OCR/blob/c21590c42881b75965e5345530b01e9084fe7a6e/config.json
  - https://huggingface.co/api/models/StarDoc-AI/NaviDC-OCR
source_type: primary
retrieved: 2026-08-29
---

# Models, dependencies, and licensing

Package Python constraint: `>=3.10,<3.13`. Major pinned ranges include torch 2.8, torchvision 0.23, transformers 4.57, tokenizers 0.22, vLLM 0.11, and xFormers 0.0.32. PDF/image processing uses Pillow, OpenCV, pypdfium2, PyMuPDF, and pypdf.

Checkpoint facts: 1,415,072,768 BF16 parameters, Qwen2.5-VL-compatible custom Transformers architecture, 128,000 configured positional limit, and Chinese/English/Japanese metadata. Upstream runtime defaults to 16,384 model length, not 128,000.

Hugging Face declares Apache-2.0. GitHub README shows an Apache-2.0 badge and links `LICENSE`, but the inspected repository tree contains no license file. Confirm licensing before redistribution or production deployment.

Transformers loading uses `trust_remote_code=True`. Pin checkpoint revision, review custom code, and isolate execution.

