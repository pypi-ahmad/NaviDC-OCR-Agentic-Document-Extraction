---
title: NaviDC-OCR system and research design
source_urls:
  - https://arxiv.org/abs/2608.12898v2
  - https://arxiv.org/html/2608.12898v2
  - https://github.com/caipeng328/NaviDC-OCR/tree/2e79d29bf32d4e8997b7cbd2ee619a12bfc8d616
source_type: primary
retrieved: 2026-08-29
---

# System and research design

NaviDC-OCR targets unified parsing of digital and camera-captured documents. It retains a high-resolution decoupled workflow, layout prediction followed by region-level content parsing, while training the model to represent warped geometry.

Paper contributions:

- multi-node consensus voting for pseudo-label construction;
- deformation-aware synthetic data;
- CGDP sampling, which allocates more polygon points around greater curvature;
- image-to-image validation using rendered structured predictions;
- progressive alignment, deformation, structure/content, and reinforcement-learning stages;
- separate structure supervision for formula syntax and OTSL table topology.

The reported model combines a Qwen2.5-VL-derived vision encoder, Qwen3-0.6B language model, and MLP aligner. These architectural facts come from the paper; checkpoint configuration uses the Transformers class name `Qwen2_5_VLForConditionalGeneration` because released custom code implements the composite model through that interface.

Reported scores, not reproduced here: 96.87 OmniDocBench v1.6, 88.53 Wild-OmniDocBench, 78.41 PureDocBench, and first place in ICDAR 2026 Sci-ImageMiner.

