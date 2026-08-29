---
chunk_id: navidc-ocr-inputs-outputs
topics: [inputs, outputs, formats]
evidence: verified
source_urls: [https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/tools/read_file.py, https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/engine.py]
---

# Inputs and outputs

Byte-detected inputs: PDF, PNG, JPEG/JPG, JP2, WebP, GIF, BMP, and TIFF. CLI accepts an input directory and result directory. Output per document: Markdown, intermediate JSON, layout PDF, and extracted image files. `do_parse` and `aio_do_parse` return intermediate JSON.

