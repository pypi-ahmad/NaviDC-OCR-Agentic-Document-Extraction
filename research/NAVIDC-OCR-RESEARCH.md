# NaviDC-OCR research report

Research date: 2026-08-29  
Upstream code revision inspected: [`2e79d29`](https://github.com/caipeng328/NaviDC-OCR/tree/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616)  
Paper version inspected: [arXiv:2608.12898v2](https://arxiv.org/abs/2608.12898v2)

## Executive summary

NaviDC-OCR is an approximately 1.2B-parameter vision-language document parser designed to handle both digital pages and camera-captured pages. The paper describes a hybrid, decoupled pipeline: a VLM first predicts layout regions, then crops are parsed with task-specific prompts for text, tables, formulas, and code. Its main research contribution is adding deformation-aware layout modeling to this high-resolution two-step design rather than requiring a separate dewarping model. The released inference package converts PDFs or supported images into page images, performs layout detection and region extraction, post-processes structured elements, and writes Markdown, intermediate JSON, extracted images, and a layout-annotated PDF.[^paper][^readme][^client][^engine]

For this repository, NaviDC-OCR is a plausible local OCR/parser engine, but integration should be treated as an adapter project, not a drop-in Python call. The upstream package has a large CUDA-oriented dependency surface, defaults to an in-process asynchronous vLLM engine, trusts remote model code, and exposes filesystem-oriented batch inference rather than an HTTP API. No application source exists in this repository yet, so integration recommendations below are design inferences, not verified compatibility claims.

## Purpose and scope

The authors frame document parsing as conversion of unstructured document images into structured, machine-readable representations. They target two regimes with one model:

- high-resolution digital documents, where explicit layout detection and crop-level parsing preserve detail;
- camera-captured documents, where curvature and perspective distortion can break conventional box-based layout analysis.[^paper]

The released model card lists Chinese, English, and Japanese, an `image-text-to-text` pipeline, and Apache-2.0 metadata. These are model-card declarations, not independently reproduced capability tests.[^hf-api]

## Architecture and runtime pipeline

### Model

The paper says NaviDC-OCR combines a vision encoder inherited from Qwen2.5-VL, a Qwen3-0.6B language model, and a newly trained MLP aligner. The released checkpoint reports 1,415,072,768 BF16 parameters. Its config identifies `Qwen2_5_VLForConditionalGeneration`, 28 text layers, hidden size 1024, a 32-layer vision encoder, and a 128,000-position architectural limit.[^paper-html][^hf-config][^hf-api]

The inference package deliberately sets a smaller default `MAX_MODEL_LEN=16384`; architectural capacity must not be confused with the shipped runtime setting.[^config]

### Inference flow

1. `infer.py` enumerates files in an input directory, reads bytes, and wraps supported images as single-page PDFs.[^infer][^read-file]
2. `engine.py` normalizes selected PDF pages, creates one output directory per input, and calls synchronous or asynchronous document analysis.[^engine]
3. The analyzer rasterizes pages through pypdfium2 or PyMuPDF and invokes a two-step VLM flow.[^pdf][^analyze]
4. A page resized to 1036 x 1036 receives the layout prompt. The parser converts model text into typed regions and normalized geometry.[^client]
5. Region crops receive type-specific prompts. Tables use OTSL, formulas use LaTeX, while text and code use direct transcription prompts. Images, lists, and equation blocks are skipped by the crop extraction path.[^client]
6. Post-processing cleans equations, converts OTSL tables to HTML, assembles page content into Markdown, saves extracted images, records intermediate JSON, and draws a layout PDF.[^post][^engine]

This is a decoupled parser even though a single checkpoint serves both steps. Layout errors can still cascade into crop parsing. Deformation-aware training and CGDP polygon sampling are intended to reduce that failure mode.[^paper-html]

## Data and training design

The paper describes three data-engine stages:

- multi-node consensus voting combines heterogeneous parser predictions into pseudo-labels;
- deformation-aware synthesis produces curved and perspective-distorted training examples;
- a Qwen2.5-VL-7B-Instruct-based self-judgement model compares original document images with renderings of predicted structure, changing verification from image-to-text to image-to-image consistency.[^paper-html]

Training progresses through four stages: vision-language alignment, deformation-aware region supervision, content-structure decoupled learning, and GRPO reinforcement learning. Formula structure labels come from LaTeX syntax extraction; table structure learning removes cell content while retaining OTSL topology tokens. GRPO uses task-specific rewards: normalized edit similarity for text, TEDS for tables, and CDM for formulas.[^paper-html]

## Reported evaluation

The authors report overall scores of 96.87 on OmniDocBench v1.6, 88.53 on Wild-OmniDocBench, and 78.41 on PureDocBench, plus first place in the ICDAR 2026 Sci-ImageMiner Challenge.[^paper] These are author-reported results, not reproduced in this research. The repository also warns that its benchmark metrics depend on particular OmniDocBench Docker evaluation paths and recommends `LAYOUT_MODE="Segmentation"` for real-world degraded tracks.[^readme]

## Setup and runtime contract

Verified upstream constraints:

- Package metadata requires Python `>=3.10,<3.13`, despite the README's looser phrase "Python 3.10+".[^pyproject][^readme]
- Upstream installation uses `pip install -e .`; a uv-based integration should translate this to project-managed dependencies rather than copy that command unchanged.[^readme]
- Declared core runtime pins include PyTorch 2.8, Transformers 4.57, vLLM 0.11, xFormers 0.0.32, Pillow, NumPy, OpenCV, PyMuPDF, pypdfium2, FastAPI, and several network/cloud utilities.[^pyproject]
- Default configuration selects `StarDoc-AI/NaviDC-OCR`, `vllm-async-engine`, detection layout mode, 16,384 maximum model length, 95% GPU-memory utilization, and pypdfium2.[^config]
- The README requires a CUDA-enabled environment for GPU inference. The Transformers backend contains a CPU fallback using float32, but upstream documentation does not establish it as a practical supported deployment for this model.[^readme][^model]
- Transformers loads both processor and model with `trust_remote_code=True`. That executes code supplied with the checkpoint and requires an explicit trust decision before production use.[^model][^hf-config]

## Inputs and outputs

Supported byte-detected inputs are PDF plus PNG, JPEG, JP2, WebP, GIF, BMP, JPG, and TIFF. The CLI accepts a directory, not an individual path or upload object. It excludes only `.json` and `.html` during enumeration, so other unsupported files reach `read_fn` and fail per file.[^infer][^read-file]

For input stem `document`, default output is:

```text
<result-root>/document/
  document.md
  document_middle.json
  document_layout.pdf
  images/
```

The callable `do_parse` and `aio_do_parse` also return intermediate JSON in memory. The JSON has `pdf_info`, `_backend: "vlm"`, and a package version field; each page contains content blocks and page metadata.[^engine][^middle]

## Limitations and risks

### Verified from primary sources

- No test suite or CI workflow exists at inspected revision. Reproducibility currently depends on manual execution and benchmark claims.
- The repository README links to `LICENSE`, but no `LICENSE` file exists in the inspected Git tree. Hugging Face metadata says Apache-2.0. License intent is clear, but repository licensing is incomplete until the owner adds the actual text.[^readme][^hf-api][^tree]
- The default backend targets CUDA/vLLM and reserves 95% GPU memory. This can conflict with an application process sharing the same GPU.[^config]
- Input processing is sequential at the top-level CLI even in async mode: its loop awaits each document before moving to the next. Async concurrency is primarily inside page/region processing.[^infer][^client]
- The paper does not provide a dedicated limitations section in v2. Its reported gains therefore should not be read as coverage of handwriting, every language, adversarial documents, or deterministic schema extraction.
- `trust_remote_code=True` increases supply-chain risk.[^model]

### Inferences requiring validation

- Windows-native vLLM deployment is likely the main environment risk. Validate upstream vLLM platform support before choosing in-process integration; WSL2/Linux service isolation may be simpler.
- A 1.415B BF16 checkpoint has about 2.8 GB of raw weight storage, but practical VRAM will be higher because activations, KV cache, image tokens, and vLLM allocation are additional. Measure on target documents.
- Markdown and generic middle JSON are useful extraction intermediates, but an agentic document-extraction system will still need deterministic mapping, validation, and confidence/error handling for domain schemas.

## Integration recommendation for this repository

No application code or project metadata is present here as of this research, so the smallest safe path is a spike behind a narrow parser boundary:

1. Run NaviDC-OCR as an isolated Linux/WSL2 worker or service, pinned to the inspected checkpoint revision. Avoid importing its entire dependency graph into a future Streamlit/UI process.
2. Define one stable request contract: document bytes plus optional page selection. Define one response contract: Markdown, middle JSON, extracted image references, warnings, and timing.
3. Preserve `middle_json` as source evidence. Convert it into domain-specific agent inputs in a separate deterministic adapter.
4. Test three seams before expanding: one digital PDF, one camera-captured page, and one page containing a table plus formula. Compare content, reading order, geometry, and table HTML against manually checked fixtures.
5. Add resource controls before multi-user use: upload limits, page/pixel limits, request timeout, bounded concurrency, and worker isolation. Upstream has `MAX_PIXELS` and concurrency knobs, but the host application must enforce its own trust boundary.[^config][^client]

Do not begin with model fine-tuning or an agent deciding OCR strategy. First establish whether the released parser meets accuracy, latency, VRAM, and structured-output needs on representative local documents.

## Reproduction record

- Firecrawl search result: [`.firecrawl/search-navidc-ocr-scraped.json`](../.firecrawl/search-navidc-ocr-scraped.json), 10 results, non-empty.
- Primary repository cloned at commit `2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616` into a temporary directory and inspected without installing dependencies.
- arXiv abstract and experimental HTML v2 inspected.
- Hugging Face model API, model card, `config.json`, and `generation_config.json` inspected.
- No model weights downloaded; no inference or benchmark was run.

## Sources

[^paper]: Peng Cai et al., ["NaviDC-OCR: Navigating Document Parsing Across Digital and Camera-Captured Documents," arXiv:2608.12898v2](https://arxiv.org/abs/2608.12898v2), submitted 2026-08-13, revised 2026-08-18.
[^paper-html]: Authors' [experimental HTML paper](https://arxiv.org/html/2608.12898v2), especially sections 3 and 4.
[^readme]: Upstream [README at inspected commit](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/README.md).
[^tree]: Upstream [Git tree at inspected commit](https://github.com/caipeng328/NaviDC-OCR/tree/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616).
[^pyproject]: Upstream [`pyproject.toml`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/pyproject.toml).
[^infer]: Upstream [`infer.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/infer.py).
[^config]: Upstream [`NaviOCR/config.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/config.py).
[^engine]: Upstream [`NaviOCR/engine.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/engine.py).
[^analyze]: Upstream [`NaviOCR/src/vlm_analyze.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/src/vlm_analyze.py).
[^client]: Upstream [`NaviOCR/vlm_utils/NaviOCR_client.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/vlm_utils/NaviOCR_client.py).
[^model]: Upstream [`NaviOCR/vlm_utils/NaviOCR_model.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/vlm_utils/NaviOCR_model.py).
[^read-file]: Upstream [`NaviOCR/tools/read_file.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/tools/read_file.py).
[^pdf]: Upstream [`NaviOCR/tools/pdf_image_tools.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/tools/pdf_image_tools.py).
[^post]: Upstream [`NaviOCR/vlm_utils/post_process/__init__.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/vlm_utils/post_process/__init__.py).
[^middle]: Upstream [`NaviOCR/src/model_output_to_middle_json.py`](https://github.com/caipeng328/NaviDC-OCR/blob/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616/NaviOCR/src/model_output_to_middle_json.py).
[^hf-config]: Official checkpoint [`config.json`](https://huggingface.co/StarDoc-AI/NaviDC-OCR/blob/c21590c42881b75965e5345530b01e9084fe7a6e/config.json).
[^hf-api]: Official [Hugging Face model API metadata](https://huggingface.co/api/models/StarDoc-AI/NaviDC-OCR).

