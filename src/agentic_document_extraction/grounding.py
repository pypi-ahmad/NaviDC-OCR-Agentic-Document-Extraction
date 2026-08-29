from __future__ import annotations

import html
import re
from collections.abc import Iterator
from difflib import SequenceMatcher
from html.parser import HTMLParser
from typing import Any

from .models import EvidenceBlock, EvidenceRef


def build_evidence_blocks(
    middle_json: dict[str, Any], source_pages: list[int]
) -> tuple[EvidenceBlock, ...]:
    blocks: list[EvidenceBlock] = []
    pages = middle_json.get("pdf_info", [])
    if not isinstance(pages, list):
        return ()
    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        source_page = source_pages[page_index] if page_index < len(source_pages) else page_index + 1
        para_blocks = page.get("para_blocks", [])
        if not isinstance(para_blocks, list):
            continue
        for block_index, block in enumerate(para_blocks):
            if not isinstance(block, dict):
                continue
            text = _collect_block_text(block).strip()
            bbox = _bbox(block.get("bbox"))
            if text and bbox is not None:
                blocks.append(
                    EvidenceBlock(
                        block_id=f"p{source_page}-b{block_index}",
                        page=source_page,
                        block_type=str(block.get("type", "unknown")),
                        bbox=bbox,
                        text=text,
                    )
                )
    return tuple(blocks)


def resolve_evidence(
    field_path: str, quote: str, page: int | None, blocks: tuple[EvidenceBlock, ...]
) -> EvidenceRef:
    normalized_quote = normalize_text(quote)
    candidates = [block for block in blocks if page is None or block.page == page]
    best: EvidenceBlock | None = None
    best_score = 0.0
    for block in candidates:
        normalized_block = normalize_text(block.text)
        if normalized_quote and normalized_quote in normalized_block:
            score = 1.0
        elif normalized_block and normalized_block in normalized_quote:
            score = min(0.98, len(normalized_block) / max(len(normalized_quote), 1) + 0.35)
        else:
            score = SequenceMatcher(None, normalized_quote, normalized_block).ratio()
        if score > best_score:
            best, best_score = block, score
    matched = best if best_score >= 0.90 else None
    return EvidenceRef(
        field_path=field_path,
        quote=quote,
        page=matched.page if matched else page,
        block_id=matched.block_id if matched else None,
        bbox=matched.bbox if matched else None,
        match_score=round(best_score if matched else 0.0, 4),
    )


def iter_leaf_values(value: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from iter_leaf_values(child, f"{path}/{escaped}")
    elif isinstance(value, list):
        if not value:
            yield path or "/", value
        else:
            for index, child in enumerate(value):
                yield from iter_leaf_values(child, f"{path}/{index}")
    else:
        yield path or "/", value


def normalize_text(value: str) -> str:
    return " ".join(html.unescape(value).casefold().split())


def _bbox(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, list) or len(value) < 4:
        return None
    try:
        coordinates = [float(item) for item in value]
    except (TypeError, ValueError):
        return None
    xs, ys = coordinates[0::2], coordinates[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def _collect_block_text(value: Any) -> str:
    parts: list[str] = []
    if isinstance(value, dict):
        content = value.get("content")
        if isinstance(content, str):
            parts.append(content)
        raw_html = value.get("html")
        if isinstance(raw_html, str):
            parts.append(_html_text(raw_html))
        for key in ("lines", "spans", "blocks", "children"):
            if key in value:
                nested = _collect_block_text(value[key])
                if nested:
                    parts.append(nested)
    elif isinstance(value, list):
        parts.extend(text for item in value if (text := _collect_block_text(item)))
    return "\n".join(parts)


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def _html_text(value: str) -> str:
    parser = _TextParser()
    parser.feed(re.sub(r"<(br|/tr|/td|/th)>", " ", value, flags=re.IGNORECASE))
    parser.close()
    return " ".join(parser.parts)
