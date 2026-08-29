# Knowledge base: NaviDC-OCR

## Summary

Primary-source reference and RAG corpus for evaluating NaviDC-OCR as the OCR/parser layer of this repository. Facts are pinned to upstream code commit `2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616`, checkpoint commit `c21590c42881b75965e5345530b01e9084fe7a6e`, and paper v2.

## Reference notes

- [System and research design](sources/system-and-research-design.md)
- [Runtime and integration contract](sources/runtime-and-integration.md)
- [Models, dependencies, and licensing](sources/models-dependencies-licensing.md)
- [Evidence quality and limitations](sources/evidence-and-limitations.md)

## RAG chunks

- [Purpose and model](chunks/01-purpose-model.md)
- [Data engine and training](chunks/02-data-training.md)
- [Inference pipeline](chunks/03-inference-pipeline.md)
- [Inputs and outputs](chunks/04-inputs-outputs.md)
- [Runtime and dependencies](chunks/05-runtime-dependencies.md)
- [Integration and risks](chunks/06-integration-risks.md)

Machine-readable provenance is in [`sources.json`](sources.json); chunk inventory is in [`manifest.json`](manifest.json).

## Coverage

- 4 normalized reference notes
- 6 topic chunks
- 15 primary source records
- 1 secondary-discovery classification for ignored search results
- 1 full research report at [`../../research/NAVIDC-OCR-RESEARCH.md`](../../research/NAVIDC-OCR-RESEARCH.md)

## Usage notes

Retrieve one or two chunks by topic, then follow their `source_urls` before making consequential architecture or licensing decisions. Treat all integration statements marked `inference` as proposals requiring a local spike. Do not use the benchmark chunk as evidence that performance has been reproduced.

## Rerun inputs

```yaml
workflow: firecrawl-knowledge-base
source:
  topic: NaviDC-OCR
  repository: https://github.com/caipeng328/NaviDC-OCR
  paper: https://arxiv.org/abs/2608.12898v2
  model: https://huggingface.co/StarDoc-AI/NaviDC-OCR
goal: reference-and-rag
depth: thorough
output_dir: knowledge-base/navidc-ocr
firecrawl_search_output: .firecrawl/search-navidc-ocr-scraped.json
```

