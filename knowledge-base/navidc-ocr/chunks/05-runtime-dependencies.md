---
chunk_id: navidc-ocr-runtime-dependencies
topics: [python, cuda, vllm, dependencies, configuration]
evidence: verified
source_urls: [https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/pyproject.toml, https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/config.py]
---

# Runtime and dependencies

Python metadata requires 3.10 through 3.12. Defaults: `vllm-async-engine`, 16,384 model length, 0.95 GPU-memory utilization, detection layout, and pypdfium2. Core stack pins torch 2.8, transformers 4.57, vLLM 0.11, xFormers 0.0.32, plus image/PDF and service libraries. Transformers can select float32 on CPU, but upstream asks for CUDA and provides no practical CPU benchmark.

