# Frequently asked questions

## Does processing leave this machine?

The application sends selected pages only to the local NaviDC worker at `127.0.0.1:8742`. It does not implement a cloud OCR call. Normal operating-system, package-management, or model-download activity is outside the extraction request path.

## Is NaviDC-OCR running in BF16?

The validated local NaviDC/vLLM runtime loads this model in BF16 on the RTX 4060 Laptop GPU. The Streamlit application does not override model dtype.

## Do I need PP-LayoutV3?

No. NaviDC-OCR includes its own layout analysis. See [How to improve extraction accuracy](how-to-improve-accuracy.md#avoid-unrelated-layout-engines).

## Why are there two Python environments?

The Streamlit environment stays small while the WSL environment retains the validated GPU stack. See [ADR-001](adr/001-isolated-ocr-worker.md).

## Why is the first extraction slow?

The worker starts lazily and vLLM may load the model during the first extraction. Later requests reuse the running worker.

## Can several users extract documents at once?

The worker accepts requests but processes one extraction at a time. This protects the 8 GB GPU. The project is intended for one trusted local user, not multi-user hosting.

## Where are uploads and results stored?

The worker uses a temporary directory that is removed after each request. Final artifacts live in the active Streamlit session and in any files you download. The application has no result database.

## Why did my result disappear?

Changing the file, selected page range, or layout mode invalidates the current result. Ending the browser session also discards session-held artifacts. Download the ZIP before changing inputs.

## Does TIFF support multiple frames?

No. The first TIFF frame is treated as one page.

## Can I process more than 25 pages?

Yes, but the UI warns because large ranges take longer and may increase GPU memory pressure. Smaller ranges are safer and easier to review.

## Can I expose the app on a network?

The current security model is local and trusted. Read [Security guidance](../SECURITY.md) before changing network exposure.
