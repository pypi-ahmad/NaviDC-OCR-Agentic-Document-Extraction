---
chunk_id: navidc-ocr-integration-risks
topics: [integration, risks, agentic-extraction]
evidence: mixed
source_urls: [https://github.com/caipeng328/NaviDC-OCR/tree/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616, https://huggingface.co/StarDoc-AI/NaviDC-OCR/blob/c21590c42881b75965e5345530b01e9084fe7a6e/config.json]
---

# Integration and risks

Verified risks: remote checkpoint code executes through `trust_remote_code=True`; upstream has no tests/CI; repository license file is missing; GPU defaults are aggressive; outputs are generic Markdown/middle JSON.

Integration inference: isolate NaviDC-OCR behind a worker contract, pin code and checkpoint revisions, validate three representative document fixtures, enforce upload/page/pixel/time/concurrency limits, and map middle JSON to domain schemas with deterministic code. Do not couple a Streamlit or agent process directly to vLLM globals until resource behavior is measured.

