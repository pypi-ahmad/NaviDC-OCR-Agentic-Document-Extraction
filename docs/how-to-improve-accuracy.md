# How to improve extraction accuracy

Use this guide when text, tables, or reading order are incomplete or incorrect.

## Prepare the best source

1. Prefer the original scan over a screenshot or recompressed copy.
2. Use a source that remains clear when rendered at 300–400 DPI.
3. Rotate pages upright before upload.
4. Avoid shadows, clipped edges, blur, and severe perspective distortion.
5. Preserve contrast without crushing faint text or handwriting.

The application renders Fast and Balanced extractions at 300 DPI and Maximum at
400 DPI. Balanced and Maximum conditionally correct illumination, contrast,
compression, mild blur, and limited skew; Fast skips enhancement. Images are
normalized to a one-page PDF before this quality pipeline.

## Choose a layout mode

Start with **Auto**, the application default. It normally selects Detection and
selects Segmentation when most pages show skew, uneven illumination, or clipped-edge risk.

Try **Segmentation** when a page has:

- Densely packed regions
- Overlapping or irregular blocks
- Multi-column content that Detection orders incorrectly

Compare outputs rather than assuming one mode is universally better. Maximum mode
also compares the alternate strategy when structured validation still requires review.
Changing layout or accuracy invalidates the previous session result.

## Reduce the page range

For long or difficult PDFs:

1. Identify the failing pages in the annotated PDF.
2. Select a smaller inclusive range around those pages.
3. Extract that range separately.
4. Compare Markdown and annotations.

Smaller ranges reduce processing time, GPU memory pressure, and review effort.

## Diagnose with the artifacts

Use the artifacts in this order:

1. **Annotated PDF:** Check whether the correct regions and reading order were detected.
2. **Raw Markdown:** Check exact text, table markup, and `<!-- Page N -->` boundaries.
3. **HTML:** Check the extracted reading order, headings, tables, and page boundaries.
4. **Manifest:** Confirm the intended range and layout mode were used.

If the annotated region is wrong, the problem is usually layout detection. If the region is correct but the text is wrong, improve scan clarity or resolution.

## Avoid unrelated layout engines

PP-LayoutV3 is not part of this application. NaviDC-OCR already performs layout analysis. Adding a second layout engine would require a separate coordinate, ordering, and evaluation pipeline; it is not an accuracy toggle for the current implementation.

## Know the limit

OCR output remains probabilistic. Always review high-impact fields such as totals, dates, identifiers, signatures, and legal terms against the source image before downstream use.
