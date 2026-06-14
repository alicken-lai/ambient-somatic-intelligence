"""Searchable internal knowledge index across local artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import re
from typing import Any

from hermes.acquisition.sources import EvidenceSource, SourceRegistry


@dataclass(frozen=True)
class KnowledgeItem:
    item_id: str
    source_id: str
    source_type: str
    reference: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "reference": self.reference,
            "text": self.text,
            "metadata": self.metadata,
        }


class KnowledgeIndex:
    def __init__(self, registry: SourceRegistry | None = None):
        self.registry = registry or SourceRegistry()
        self.items: list[KnowledgeItem] = []

    def build(self) -> "KnowledgeIndex":
        self.items = []
        for source in self.registry.enabled_sources():
            self.items.extend(_items_for_source(source))
        return self

    def semantic_search(self, query: str, *, limit: int = 10) -> list[tuple[KnowledgeItem, float]]:
        query_terms = _terms(query)
        scored: list[tuple[KnowledgeItem, float]] = []
        for item in self.items:
            item_terms = _terms(item.text)
            if not item_terms:
                continue
            overlap = len(query_terms.intersection(item_terms))
            score = overlap / max(1, len(query_terms))
            if score > 0:
                scored.append((item, round(score, 4)))
        return sorted(scored, key=lambda pair: pair[1], reverse=True)[:limit]

    def metadata_search(self, **metadata: Any) -> list[KnowledgeItem]:
        return [item for item in self.items if all(item.metadata.get(key) == value for key, value in metadata.items())]

    def relationship_search(self, source_type: str) -> list[KnowledgeItem]:
        return [item for item in self.items if item.source_type == source_type]


def _items_for_source(source: EvidenceSource) -> list[KnowledgeItem]:
    paths = source.metadata.get("paths")
    if paths is None and source.metadata.get("path"):
        paths = [source.metadata["path"]]
    if not paths:
        return []
    items: list[KnowledgeItem] = []
    for pattern in paths:
        for path in _expand(pattern):
            if not path.is_file():
                continue
            text = _read_text(path)
            if not text:
                continue
            items.append(
                KnowledgeItem(
                    item_id=f"{source.source_id}:{path.as_posix()}",
                    source_id=source.source_id,
                    source_type=source.source_type,
                    reference=str(path),
                    text=text[:20000],
                    metadata={"suffix": path.suffix.lower()},
                )
            )
    return items


def _expand(pattern: str) -> list[Path]:
    path = Path(pattern)
    if any(char in pattern for char in "*?[]"):
        return sorted(Path(".").glob(pattern))
    return [path]


def _read_text(path: Path) -> str:
    try:
        if path.suffix.lower() == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            return json.dumps(raw, ensure_ascii=False)
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[A-Za-z0-9_]{4,}", text.lower())}
