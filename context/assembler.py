"""
Context Assembler — Dynamic context assembly orchestrator.

The ContextAssembler is the main entry point for building agent context.
It coordinates all other components to produce an optimally-packed context
window within token budget:

  1. Analyze the task to determine budget allocation preset
  2. Retrieve relevant memories via KernelRetriever (MemoryKernel-backed)
  3. Compress if needed via MemoryCompressor
  4. Pack into pools tracked by ContextBudgetManager
  5. Generate a ready-to-inject context block

Anti-patterns prevented:
  - No unlimited context append
  - No full repo dump
  - No naive memory injection
  - No context pollution from irrelevant retrieval
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from context.budget_manager import ContextBudgetManager, estimate_tokens
from context.memory_compressor import MemoryCompressor
from context.kernel_retriever import KernelRetriever


@dataclass
class ContextBlock:
    """An assembled context block ready for injection."""
    memory_context: str
    task_context: str
    system_context: str
    total_tokens: int
    budget_report: dict[str, Any]
    retrieval_stats: dict[str, Any]
    compression_stats: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)

    def to_prompt_sections(self) -> dict[str, str]:
        """Return context as named sections for prompt assembly."""
        sections = {}
        if self.system_context:
            sections["system"] = self.system_context
        if self.memory_context:
            sections["memory"] = self.memory_context
        if self.task_context:
            sections["task"] = self.task_context
        return sections

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_context": self.memory_context[:500] + "..." if len(self.memory_context) > 500 else self.memory_context,
            "task_context": self.task_context[:200] + "..." if len(self.task_context) > 200 else self.task_context,
            "total_tokens": self.total_tokens,
            "budget_report": self.budget_report,
            "retrieval_stats": self.retrieval_stats,
            "compression_stats": self.compression_stats,
            "warnings": self.warnings,
        }


TASK_TYPE_KEYWORDS = {
    "code_review": {"review", "pr", "diff", "changes", "look at"},
    "debugging": {"bug", "error", "fix", "crash", "broken", "failing", "debug"},
    "planning": {"plan", "design", "architect", "refactor", "migrate", "strategy"},
    "memory_heavy": {"remember", "history", "previous", "last time", "recall", "before"},
}


def detect_task_type(task_description: str) -> str:
    """Infer task type from description for budget allocation."""
    lower = task_description.lower()
    scores: dict[str, int] = {}

    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[task_type] = score

    if scores:
        return max(scores, key=scores.get)
    return "default"


class ContextAssembler:
    """
    Orchestrates context assembly for agent operations.

    Usage:
        assembler = ContextAssembler(total_tokens=128000)
        context = assembler.assemble(
            task="Fix the memory leak in dmn_tick_loop.py",
            system_prompt="You are Hermes, an ambient cognitive OS.",
            additional_context={"code": file_contents},
        )
        # Use context.to_prompt_sections() for prompt building
    """

    def __init__(
        self,
        total_tokens: int = 128_000,
        retriever: KernelRetriever | None = None,
    ):
        self.total_tokens = total_tokens
        if retriever is None:
            from kernel import get_memory_kernel
            retriever = KernelRetriever(get_memory_kernel())
        self.retriever = retriever
        self.compressor = MemoryCompressor()

    def assemble(
        self,
        task: str,
        system_prompt: str = "",
        additional_context: dict[str, str] | None = None,
        memory_query: str | None = None,
        task_type: str | None = None,
        max_memory_results: int = 15,
    ) -> ContextBlock:
        """
        Assemble a complete context block for the given task.

        Args:
            task: The task description / user instruction
            system_prompt: System-level prompt/rules
            additional_context: Extra context keyed by pool name (e.g. {"code": "..."})
            memory_query: Custom query for memory retrieval (defaults to task)
            task_type: Force a task type for budget allocation
            max_memory_results: Max memory records to retrieve
        """
        if not task_type:
            task_type = detect_task_type(task)

        budget = ContextBudgetManager(total_tokens=self.total_tokens)
        budget.apply_preset(task_type)

        # 1. System context (fixed overhead)
        system_context = ""
        if system_prompt:
            system_context = budget.allocate_text("system", system_prompt)

        # 2. Task context
        task_context = budget.allocate_text("task", task)

        # 3. Additional context (code, tool results, etc.)
        if additional_context:
            for pool_name, content in additional_context.items():
                if pool_name in budget.pools:
                    budget.allocate_text(pool_name, content)

        # 4. Memory retrieval within remaining memory budget
        memory_budget = budget.pools["memory"].remaining
        query = memory_query or task
        retrieval_result = self.retriever.retrieve_for_context(
            query=query,
            token_budget=memory_budget,
        )

        # 5. Compress if exceeds budget
        compression_stats = None
        memory_records = retrieval_result.get("results", [])

        if retrieval_result.get("total_tokens", 0) > memory_budget and memory_records:
            compressed = self.compressor.compress(
                memory_records,
                target_tokens=memory_budget,
                preserve_top_n=3,
            )
            memory_context = compressed.content
            compression_stats = compressed.to_dict()
            del compression_stats["content"]
        else:
            memory_context = self._format_memory_results(memory_records)

        budget.consume("memory", memory_context)

        # 6. Build final context block
        warnings = budget.report().get("warnings", [])
        if not memory_records:
            warnings.append("No relevant memories found for this task")

        return ContextBlock(
            memory_context=memory_context,
            task_context=task_context,
            system_context=system_context,
            total_tokens=budget.total_used,
            budget_report=budget.report(),
            retrieval_stats={
                "query": query,
                "results_count": len(memory_records),
                "top_score": retrieval_result.get("top_score", 0),
                "layers_searched": retrieval_result.get("layers_searched", []),
                "task_type_detected": task_type,
            },
            compression_stats=compression_stats,
            warnings=warnings,
        )

    def assemble_for_subagent(
        self,
        task: str,
        parent_context: str = "",
        memory_query: str | None = None,
    ) -> ContextBlock:
        """
        Assemble context for a sub-agent with tighter budget.

        Sub-agents get 50% of normal budget to leave room for their own work.
        """
        sub_budget = self.total_tokens // 2
        sub_assembler = ContextAssembler(
            total_tokens=sub_budget,
            retriever=self.retriever,
        )
        return sub_assembler.assemble(
            task=task,
            system_prompt=parent_context[:2000] if parent_context else "",
            memory_query=memory_query,
            max_memory_results=8,
        )

    def estimate_task_budget(self, task: str) -> dict[str, Any]:
        """
        Estimate budget needs for a task without actually assembling.

        Useful for planning multi-step operations.
        """
        task_type = detect_task_type(task)
        budget = ContextBudgetManager(total_tokens=self.total_tokens)
        budget.apply_preset(task_type)

        retrieval_preview = self.retriever.retrieve(task, max_results=5, token_budget=1000)
        estimated_memory_tokens = sum(r.token_estimate for r in retrieval_preview) * 3

        return {
            "task_type": task_type,
            "total_budget": self.total_tokens,
            "allocation": budget.suggest_allocation(task_type),
            "estimated_memory_tokens": estimated_memory_tokens,
            "memory_preview_count": len(retrieval_preview),
            "top_memory_score": retrieval_preview[0].score if retrieval_preview else 0,
            "recommendation": self._budget_recommendation(task_type, estimated_memory_tokens),
        }

    def _budget_recommendation(self, task_type: str, estimated_memory: int) -> str:
        """Generate a human-readable budget recommendation."""
        memory_ratio = estimated_memory / self.total_tokens
        if memory_ratio > 0.4:
            return "Heavy memory load. Consider narrowing the query or compressing history."
        if task_type == "planning":
            return "Planning task. Memory-heavy allocation applied."
        if task_type == "debugging":
            return "Debug task. Code + memory balanced allocation."
        return "Standard allocation applied."

    def _format_memory_results(self, results: list[dict[str, Any]]) -> str:
        """Format retrieval results as context text."""
        if not results:
            return ""

        parts: list[str] = []
        for r in results:
            layer = r.get("layer", "")
            score = r.get("score", 0)
            content = r.get("content", "")
            timestamp = r.get("timestamp", "")[:10]

            header = f"[{layer}|{score:.2f}]"
            if timestamp:
                header += f" ({timestamp})"

            parts.append(f"{header} {content}")

        return "\n---\n".join(parts)


if __name__ == "__main__":
    assembler = ContextAssembler(total_tokens=128_000)

    context = assembler.assemble(
        task="Fix the memory recall function to prioritize semantic layer results",
        system_prompt="You are the Ambient OS principal architect.",
    )

    output = context.to_dict()
    print(json.dumps(output, indent=2, ensure_ascii=False))
