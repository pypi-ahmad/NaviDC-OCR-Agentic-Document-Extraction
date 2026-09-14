"""Shared, immutable value objects passed between pipeline stages.

Every type here is a frozen, slotted dataclass: this module holds data only,
never validation or business logic. Behavior lives in documents.py,
quality.py, schemas.py, grounding.py, validation.py, and semantic.py. Open
documents.py next to see where the pipeline begins.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

# "verified"/"review"/"blocked" are assigned automatically by
# validation.build_field_results() from evidence and validation scores.
# "accepted"/"corrected"/"rejected" are only set by semantic.apply_manual_review()
# after a human decision.
ReviewStatus = Literal["verified", "review", "blocked", "accepted", "corrected", "rejected"]


@dataclass(frozen=True, slots=True)
class PageQuality:
    """Per-page scan-quality signals produced by quality.analyze_page().

    dpi is the render resolution the scores were computed at. skew_degrees is
    signed rotation in degrees (sign convention set by quality._estimate_skew).
    The *_score fields are unitless heuristic magnitudes tuned against the
    validated hardware, not calibrated physical units - see quality.py for the
    thresholds that turn them into warnings.
    """

    page: int
    dpi: int
    blur_score: float
    contrast_score: float
    skew_degrees: float
    skew_confidence: float
    shadow_score: float
    compression_score: float
    clipped_edge_risk: bool
    warnings: tuple[str, ...] = ()
    transformations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class QualityReport:
    policy: str
    render_dpi: int
    pages: tuple[PageQuality, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PreparedDocument:
    pdf_bytes: bytes
    quality: QualityReport


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    name: str
    version: str
    schema: dict[str, Any]
    field_guide: str = ""
    schema_hash: str = ""


@dataclass(frozen=True, slots=True)
class EvidenceBlock:
    """One OCR layout block extracted from NaviDC's middle_json for one page.

    bbox is copied through unmodified as (min_x, min_y, max_x, max_y); its
    coordinate space (pixels at a given render DPI, or PDF points) is unclear
    from this file - see grounding.build_evidence_blocks and the NaviDC-OCR
    middle.json format.
    """

    block_id: str
    page: int
    block_type: str
    bbox: tuple[float, float, float, float]
    text: str


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Resolution of one field's model-claimed quote to a real OCR block.

    block_id is None when no block matched with sufficient confidence (see
    grounding.resolve_evidence's 0.90 threshold); semantic.py treats that as
    "not grounded" and discards the field's value even if it passed schema
    validation.
    """

    field_path: str
    quote: str
    page: int | None
    block_id: str | None
    bbox: tuple[float, float, float, float] | None
    match_score: float


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    field_path: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class FieldResult:
    field_path: str
    value: Any
    evidence: EvidenceRef | None
    verification_score: float
    status: ReviewStatus
    issues: tuple[ValidationIssue, ...] = ()
    corrected: bool = False


@dataclass(frozen=True, slots=True)
class ReviewEvent:
    timestamp: str
    action: str
    field_path: str
    old_value: Any = None
    new_value: Any = None


@dataclass(frozen=True, slots=True)
class StructuredExtraction:
    """Final structured-extraction result after semantic.run_structured_extraction().

    attempts is the number of model calls made (1 plus however many bounded
    corrections ran; see semantic.py's max_corrections). review_required is
    true whenever any field failed validation or grounding, or a human
    review action is still pending - the UI uses it to prompt a review pass.
    """

    record: dict[str, Any]
    fields: tuple[FieldResult, ...]
    issues: tuple[ValidationIssue, ...]
    schema_name: str
    schema_version: str
    schema_hash: str
    model: str
    reasoning_effort: str
    attempts: int
    review_required: bool
    audit: tuple[ReviewEvent, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
