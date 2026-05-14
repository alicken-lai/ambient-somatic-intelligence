"""
Memory Compressor — Context compression strategies for token efficiency.

Compression tiers (applied in order of increasing aggressiveness):
  1. Deduplication — Remove redundant records
  2. Truncation   — Cut long content to key portions
  3. Extraction   — Pull only key-value facts from verbose records
  4. Summarization — Collapse multiple records into a single summary
  5. Elision      — Drop lowest-relevance records entirely

Each tier preserves information fidelity as much as possible while
reducing token consumption. The compressor respects a target token
budget and applies the minimum compression needed to fit.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class CompressedBlock:
    """A block of compressed context."""
    content: str
    original_tokens: int
    compressed_tokens: int
    compression_method: str
    records_included: int
    records_dropped: int = 0

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.compressed_tokens / self.original_tokens)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": round(self.compression_ratio, 3),
            "method": self.compression_method,
            "records_included": self.records_included,
            "records_dropped": self.records_dropped,
        }


CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    cjk = len(CJK_RE.findall(text))
    non_cjk = len(text) - cjk
    return int(cjk * 0.7 + non_cjk / 4)


class MemoryCompressor:
    """
    Compresses memory records to fit within a token budget.

    Usage:
        compressor = MemoryCompressor()
        result = compressor.compress(records, target_tokens=5000)
        print(result.content)
    """

    def compress(
        self,
        records: list[dict[str, Any]],
        target_tokens: int,
        preserve_top_n: int = 3,
    ) -> CompressedBlock:
        """
        Compress records to fit within target token budget.

        Args:
            records: List of memory records (with 'content', 'score', etc.)
            target_tokens: Maximum tokens for output
            preserve_top_n: Always keep top N records uncompressed
        """
        if not records:
            return CompressedBlock(
                content="",
                original_tokens=0,
                compressed_tokens=0,
                compression_method="none",
                records_included=0,
            )

        original_tokens = sum(_estimate_tokens(r.get("content", "")) for r in records)

        if original_tokens <= target_tokens:
            content = self._format_records(records)
            return CompressedBlock(
                content=content,
                original_tokens=original_tokens,
                compressed_tokens=_estimate_tokens(content),
                compression_method="none",
                records_included=len(records),
            )

        result = self._tier1_dedup(records)
        if _estimate_tokens(self._format_records(result)) <= target_tokens:
            content = self._format_records(result)
            return CompressedBlock(
                content=content,
                original_tokens=original_tokens,
                compressed_tokens=_estimate_tokens(content),
                compression_method="deduplication",
                records_included=len(result),
                records_dropped=len(records) - len(result),
            )

        result = self._tier2_truncate(result, target_tokens, preserve_top_n)
        if _estimate_tokens(self._format_records(result)) <= target_tokens:
            content = self._format_records(result)
            return CompressedBlock(
                content=content,
                original_tokens=original_tokens,
                compressed_tokens=_estimate_tokens(content),
                compression_method="truncation",
                records_included=len(result),
                records_dropped=len(records) - len(result),
            )

        result = self._tier3_extract(result, target_tokens, preserve_top_n)
        if _estimate_tokens(self._format_records(result)) <= target_tokens:
            content = self._format_records(result)
            return CompressedBlock(
                content=content,
                original_tokens=original_tokens,
                compressed_tokens=_estimate_tokens(content),
                compression_method="extraction",
                records_included=len(result),
                records_dropped=len(records) - len(result),
            )

        content = self._tier4_summarize(result, target_tokens, preserve_top_n)
        return CompressedBlock(
            content=content,
            original_tokens=original_tokens,
            compressed_tokens=_estimate_tokens(content),
            compression_method="summarization",
            records_included=len(result),
            records_dropped=len(records) - len(result),
        )

    def _tier1_dedup(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove records with near-identical content."""
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for record in records:
            content = record.get("content", "")
            key = content[:200].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(record)
        return deduped

    def _tier2_truncate(
        self,
        records: list[dict[str, Any]],
        target_tokens: int,
        preserve_top_n: int,
    ) -> list[dict[str, Any]]:
        """Truncate long records, keeping first/last portions."""
        per_record_budget = target_tokens // max(len(records), 1)
        char_budget = int(per_record_budget * 3.5)

        result: list[dict[str, Any]] = []
        for i, record in enumerate(records):
            content = record.get("content", "")
            if i < preserve_top_n or len(content) <= char_budget:
                result.append(record)
            else:
                head = content[: char_budget // 2]
                tail = content[-(char_budget // 4):]
                truncated = f"{head}\n[...truncated...]\n{tail}"
                result.append({**record, "content": truncated})

        return result

    def _tier3_extract(
        self,
        records: list[dict[str, Any]],
        target_tokens: int,
        preserve_top_n: int,
    ) -> list[dict[str, Any]]:
        """Extract only key facts from records."""
        result: list[dict[str, Any]] = []
        for i, record in enumerate(records):
            if i < preserve_top_n:
                result.append(record)
                continue

            content = record.get("content", "")
            extracted = self._extract_key_facts(content)
            tags = record.get("tags", [])
            layer = record.get("layer", "")
            compact = f"[{layer}] {', '.join(tags)}: {extracted}"
            result.append({**record, "content": compact})

        total = sum(_estimate_tokens(r.get("content", "")) for r in result)
        if total > target_tokens:
            keep = max(preserve_top_n, len(result) // 2)
            result = result[:keep]

        return result

    def _extract_key_facts(self, content: str) -> str:
        """Extract key facts from verbose content."""
        if len(content) <= 200:
            return content

        try:
            data = json.loads(content)
            if isinstance(data, dict):
                important_keys = {"type", "status", "error", "result", "action", "summary"}
                facts = {k: v for k, v in data.items() if k in important_keys}
                if facts:
                    return json.dumps(facts, ensure_ascii=False)
                return json.dumps({k: v for k, v in list(data.items())[:5]}, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            pass

        sentences = re.split(r"[.。\n]", content)
        key_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:3]
        return ". ".join(key_sentences) if key_sentences else content[:200]

    def _tier4_summarize(
        self,
        records: list[dict[str, Any]],
        target_tokens: int,
        preserve_top_n: int,
    ) -> str:
        """Create a dense summary of all records."""
        preserved = records[:preserve_top_n]
        rest = records[preserve_top_n:]

        parts: list[str] = []

        for record in preserved:
            content = record.get("content", "")[:500]
            layer = record.get("layer", "?")
            parts.append(f"[{layer}] {content}")

        if rest:
            layers_summary: dict[str, int] = {}
            all_tags: set[str] = set()
            for r in rest:
                layer = r.get("layer", "unknown")
                layers_summary[layer] = layers_summary.get(layer, 0) + 1
                all_tags.update(r.get("tags", []))

            layer_str = ", ".join(f"{l}:{c}" for l, c in layers_summary.items())
            tags_str = ", ".join(sorted(all_tags)[:15])
            parts.append(f"\n[+{len(rest)} additional records: {layer_str}]")
            parts.append(f"[Related tags: {tags_str}]")

        content = "\n---\n".join(parts)

        if _estimate_tokens(content) > target_tokens:
            char_limit = int(target_tokens * 3.5)
            content = content[:char_limit] + "\n[...context budget exceeded, content truncated...]"

        return content

    def _format_records(self, records: list[dict[str, Any]]) -> str:
        """Format records for context injection."""
        parts: list[str] = []
        for record in records:
            content = record.get("content", "")
            layer = record.get("layer", "")
            timestamp = record.get("timestamp", "")[:10]
            score = record.get("score", 0)

            header = f"[{layer}]"
            if timestamp:
                header += f" ({timestamp})"
            if score:
                header += f" relevance:{score:.2f}"

            parts.append(f"{header}\n{content}")

        return "\n---\n".join(parts)


if __name__ == "__main__":
    test_records = [
        {"content": "Cursor MCP setup: use /opt/homebrew/bin/hermes mcp serve with PYTHONPATH", "layer": "procedural", "tags": ["cursor", "mcp"], "score": 0.94, "timestamp": "2026-05-13"},
        {"content": "Guardian rule: all write operations must pass guardian_check first", "layer": "governance", "tags": ["guardian", "rule"], "score": 0.85, "timestamp": "2026-05-13"},
        {"content": "Memory architecture: 6 layers (episodic/semantic/procedural/governance/scratchpad/archive)", "layer": "semantic", "tags": ["architecture", "memory"], "score": 0.80, "timestamp": "2026-05-13"},
    ]

    compressor = MemoryCompressor()
    result = compressor.compress(test_records, target_tokens=500)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
