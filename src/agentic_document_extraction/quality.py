from __future__ import annotations

from dataclasses import replace
from typing import Literal

import cv2
import numpy as np
import pymupdf

from .models import PageQuality, PreparedDocument, QualityReport

AccuracyMode = Literal["Fast", "Balanced", "Maximum"]


def prepare_document(
    pdf_bytes: bytes, source_pages: list[int], policy: AccuracyMode
) -> PreparedDocument:
    """Rasterize, assess, and conservatively improve selected source pages."""
    render_dpi = 400 if policy == "Maximum" else 300
    source = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    prepared = pymupdf.open()
    quality_pages: list[PageQuality] = []
    try:
        for index in range(source.page_count):
            page = source[index]
            source_page = source_pages[index] if index < len(source_pages) else index + 1
            pixmap = page.get_pixmap(dpi=render_dpi, alpha=False, colorspace=pymupdf.csRGB)
            image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                pixmap.height, pixmap.width, pixmap.n
            )
            if pixmap.n == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            report = analyze_page(image, source_page, render_dpi)
            output = image
            transformations: list[str] = []
            if policy != "Fast":
                output, transformations = enhance_page(image, report)
            report = replace(report, transformations=tuple(transformations))
            quality_pages.append(report)
            ok, encoded = cv2.imencode(".png", cv2.cvtColor(output, cv2.COLOR_RGB2BGR))
            if not ok:
                raise RuntimeError("Could not encode a prepared document page.")
            target = prepared.new_page(width=page.rect.width, height=page.rect.height)
            target.insert_image(target.rect, stream=encoded.tobytes())
        prepared_bytes = prepared.tobytes(garbage=4, deflate=True)
    finally:
        prepared.close()
        source.close()
    return PreparedDocument(
        pdf_bytes=prepared_bytes,
        quality=QualityReport(policy=policy, render_dpi=render_dpi, pages=tuple(quality_pages)),
    )


def analyze_page(image: np.ndarray, page: int, dpi: int) -> PageQuality:
    sample = _diagnostic_sample(image)
    gray = cv2.cvtColor(sample, cv2.COLOR_RGB2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast = float(gray.std())
    skew, skew_confidence = _estimate_skew(gray)
    background = cv2.GaussianBlur(gray, (0, 0), 35)
    shadow = float(background.std() / max(background.mean(), 1.0))
    compression = _blockiness(gray)
    clipped = _clipped_edge_risk(gray)
    warnings: list[str] = []
    if blur < 70:
        warnings.append("blur")
    if contrast < 32:
        warnings.append("low_contrast")
    if abs(skew) >= 0.5 and skew_confidence >= 0.6:
        warnings.append("skew")
    if shadow > 0.12:
        warnings.append("uneven_illumination")
    if compression > 1.35:
        warnings.append("compression")
    if clipped:
        warnings.append("clipped_edge_risk")
    return PageQuality(
        page=page,
        dpi=dpi,
        blur_score=round(blur, 2),
        contrast_score=round(contrast, 2),
        skew_degrees=round(skew, 3),
        skew_confidence=round(skew_confidence, 3),
        shadow_score=round(shadow, 4),
        compression_score=round(compression, 3),
        clipped_edge_risk=clipped,
        warnings=tuple(warnings),
    )


def enhance_page(image: np.ndarray, report: PageQuality) -> tuple[np.ndarray, list[str]]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    transformations: list[str] = []
    if "uneven_illumination" in report.warnings:
        background = cv2.GaussianBlur(gray, (0, 0), max(35, min(gray.shape) // 30))
        gray = cv2.divide(gray, background, scale=245)
        transformations.append("illumination_normalization")
    if "low_contrast" in report.warnings:
        gray = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8)).apply(gray)
        transformations.append("contrast_enhancement")
    if "compression" in report.warnings:
        gray = cv2.fastNlMeansDenoising(gray, None, 5, 7, 21)
        transformations.append("light_denoise")
    if "blur" in report.warnings and report.blur_score >= 25:
        softened = cv2.GaussianBlur(gray, (0, 0), 1.0)
        gray = cv2.addWeighted(gray, 1.35, softened, -0.35, 0)
        transformations.append("mild_sharpen")
    if "skew" in report.warnings and abs(report.skew_degrees) <= 7:
        height, width = gray.shape
        matrix = cv2.getRotationMatrix2D((width / 2, height / 2), report.skew_degrees, 1.0)
        gray = cv2.warpAffine(
            gray,
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )
        transformations.append("deskew")
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB), transformations


def recommend_layout(report: QualityReport) -> str:
    degraded = sum(
        bool({"skew", "uneven_illumination", "clipped_edge_risk"} & set(page.warnings))
        for page in report.pages
    )
    return "Segmentation" if degraded > len(report.pages) / 2 else "Detection"


def evidence_crop(
    pdf_bytes: bytes, page_index: int, bbox: tuple[float, float, float, float], dpi: int = 180
) -> bytes:
    document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = document[page_index]
        clip = pymupdf.Rect(*bbox) & page.rect
        if clip.is_empty:
            raise ValueError("Evidence region is outside the source page.")
        return page.get_pixmap(dpi=dpi, clip=clip, alpha=False).tobytes("png")
    finally:
        document.close()


def _diagnostic_sample(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    scale = min(1.0, 1600 / max(height, width))
    if scale == 1.0:
        return image
    return cv2.resize(
        image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA
    )


def _estimate_skew(gray: np.ndarray) -> tuple[float, float]:
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 1800,
        threshold=80,
        minLineLength=max(40, gray.shape[1] // 12),
        maxLineGap=20,
    )
    if lines is None:
        return 0.0, 0.0
    angles = []
    for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
        angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if -10 <= angle <= 10:
            angles.append(angle)
    if len(angles) < 4:
        return 0.0, 0.0
    median = float(np.median(angles))
    deviation = float(np.median(np.abs(np.asarray(angles) - median)))
    confidence = min(1.0, len(angles) / 20) * max(0.0, 1 - deviation / 3)
    return -median, confidence


def _blockiness(gray: np.ndarray) -> float:
    if min(gray.shape) < 16:
        return 0.0
    vertical = np.abs(np.diff(gray.astype(np.float32), axis=1))
    horizontal = np.abs(np.diff(gray.astype(np.float32), axis=0))
    boundary = np.mean(vertical[:, 7::8]) + np.mean(horizontal[7::8, :])
    ordinary = np.mean(vertical) + np.mean(horizontal)
    return float(boundary / max(ordinary, 1e-6))


def _clipped_edge_risk(gray: np.ndarray) -> bool:
    dark = gray < 120
    band = max(2, min(gray.shape) // 100)
    edge_density = np.mean(
        np.concatenate(
            [
                dark[:band, :].ravel(),
                dark[-band:, :].ravel(),
                dark[:, :band].ravel(),
                dark[:, -band:].ravel(),
            ]
        )
    )
    return bool(edge_density > 0.08)
