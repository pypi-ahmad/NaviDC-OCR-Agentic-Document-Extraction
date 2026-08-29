from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .grounding import iter_leaf_values, resolve_evidence
from .models import EvidenceBlock, FieldResult, ValidationIssue


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> tuple[ValidationIssue, ...]:
    validator = Draft202012Validator(_without_extensions(schema), format_checker=FormatChecker())
    issues = [
        ValidationIssue(
            field_path=_error_path(error.absolute_path),
            code=f"schema.{error.validator}",
            message=error.message,
        )
        for error in sorted(
            validator.iter_errors(record), key=lambda item: list(item.absolute_path)
        )
    ]
    rules = schema.get("x-validation-rules", [])
    if isinstance(rules, list):
        for rule in rules:
            issue = _validate_rule(record, rule)
            if issue is not None:
                issues.append(issue)
    return tuple(issues)


def build_field_results(
    record: dict[str, Any],
    evidence_payload: list[dict[str, Any]],
    blocks: tuple[EvidenceBlock, ...],
    issues: tuple[ValidationIssue, ...],
    corrected_paths: set[str] | None = None,
) -> tuple[FieldResult, ...]:
    corrected_paths = corrected_paths or set()
    evidence_by_path = {
        str(item.get("field_path")): item
        for item in evidence_payload
        if isinstance(item, dict) and item.get("field_path")
    }
    results: list[FieldResult] = []
    for path, value in iter_leaf_values(record):
        field_issues = tuple(issue for issue in issues if _path_related(path, issue.field_path))
        raw_evidence = evidence_by_path.get(path)
        evidence = None
        if value is not None and raw_evidence:
            page = raw_evidence.get("page")
            evidence = resolve_evidence(
                path,
                str(raw_evidence.get("quote", "")),
                page if isinstance(page, int) else None,
                blocks,
            )
        validation_score = 0.0 if field_issues else 1.0
        evidence_score = evidence.match_score if evidence else 0.0
        score = 0.7 * evidence_score + 0.3 * validation_score
        corrected = path in corrected_paths
        if corrected:
            score = max(0.0, score - 0.1)
        if value is None:
            score = 0.0 if field_issues else 0.3
        if evidence is None or evidence.block_id is None:
            score = min(score, 0.69)
        status = "verified" if score >= 0.9 else "review" if score >= 0.7 else "blocked"
        results.append(
            FieldResult(
                field_path=path,
                value=value,
                evidence=evidence,
                verification_score=round(score, 4),
                status=status,
                issues=field_issues,
                corrected=corrected,
            )
        )
    return tuple(results)


def objective(
    fields: tuple[FieldResult, ...], issues: tuple[ValidationIssue, ...]
) -> tuple[int, int, int]:
    valid = sum(not field.issues and field.value is not None for field in fields)
    grounded = sum(
        field.evidence is not None and field.evidence.block_id is not None for field in fields
    )
    return valid, grounded, -len(issues)


def _without_extensions(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_extensions(child)
            for key, child in value.items()
            if not key.startswith("x-")
        }
    if isinstance(value, list):
        return [_without_extensions(item) for item in value]
    return value


def _error_path(parts: Any) -> str:
    path = ""
    for part in parts:
        escaped = str(part).replace("~", "~0").replace("/", "~1")
        path += f"/{escaped}"
    return path or "/"


def _path_related(field: str, issue: str) -> bool:
    return (
        issue == "/"
        or field == issue
        or field.startswith(f"{issue}/")
        or issue.startswith(f"{field}/")
    )


def _validate_rule(record: dict[str, Any], rule: Any) -> ValidationIssue | None:
    if not isinstance(rule, dict):
        return ValidationIssue("/", "rule.invalid", "A validation rule is not an object.")
    kind = rule.get("type")
    if kind == "sum_items_equals":
        target_path, items_path, value_path = (
            rule.get("target"),
            rule.get("items"),
            rule.get("value"),
        )
        target, items = _pointer(record, target_path), _pointer(record, items_path)
        if target is None or not isinstance(items, list):
            return None
        values = [_pointer(item, value_path) for item in items]
        return _compare_sum(target_path, target, values, rule)
    if kind == "sum_fields_equals":
        target_path = rule.get("target")
        fields = rule.get("fields")
        if not isinstance(fields, list):
            return ValidationIssue("/", "rule.invalid", "sum_fields_equals requires fields.")
        target = _pointer(record, target_path)
        if target is None:
            return None
        return _compare_sum(target_path, target, [_pointer(record, item) for item in fields], rule)
    if kind == "date_order":
        start_path, end_path = rule.get("start"), rule.get("end")
        start, end = _pointer(record, start_path), _pointer(record, end_path)
        if start is None or end is None:
            return None
        try:
            valid = date.fromisoformat(str(start)) <= date.fromisoformat(str(end))
        except ValueError:
            return ValidationIssue(
                str(start_path), "rule.date_order", "Dates must use ISO YYYY-MM-DD."
            )
        if not valid:
            return ValidationIssue(
                str(end_path), "rule.date_order", "End date precedes start date."
            )
        return None
    if kind == "equals":
        left_path, right_path = rule.get("left"), rule.get("right")
        left, right = _pointer(record, left_path), _pointer(record, right_path)
        if left is not None and right is not None and left != right:
            return ValidationIssue(
                str(right_path), "rule.equals", "Designated fields do not match."
            )
        return None
    return ValidationIssue("/", "rule.unsupported", f"Unsupported validation rule: {kind}")


def _compare_sum(
    path: Any, target: Any, values: list[Any], rule: dict[str, Any]
) -> ValidationIssue | None:
    if any(value is None for value in values):
        return None
    try:
        expected = sum((Decimal(str(value)) for value in values), Decimal(0))
        actual = Decimal(str(target))
        tolerance = Decimal(str(rule.get("tolerance", 0.01)))
    except (InvalidOperation, ValueError):
        return ValidationIssue(str(path), "rule.total", "Total validation requires numeric values.")
    if abs(actual - expected) > tolerance:
        return ValidationIssue(str(path), "rule.total", f"Total does not equal {expected}.")
    return None


def _pointer(value: Any, pointer: Any) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return None
    current = value
    for raw in pointer.split("/")[1:]:
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and key.isdigit() and int(key) < len(current):
            current = current[int(key)]
        else:
            return None
    return current
