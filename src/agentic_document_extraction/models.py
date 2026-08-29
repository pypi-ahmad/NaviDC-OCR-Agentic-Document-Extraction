from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ReviewStatus = Literal["verified", "review", "blocked", "accepted", "corrected", "rejected"]


@dataclass(frozen=True, slots=True)
class PageQuality:
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
    block_id: str
    page: int
    block_type: str
    bbox: tuple[float, float, float, float]
    text: str


@dataclass(frozen=True, slots=True)
class EvidenceRef:
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
