"""
Context Engineering Layer — Ambient OS context assembly and retrieval.

Solves context entropy: the problem of limited token budgets, irrelevant retrieval,
and context pollution that degrades agent performance.

Components:
  budget_manager.py    — Token budget allocation and tracking
  semantic_retriever.py — Relevance-scored memory retrieval with layer priority
  kernel_retriever.py   — MemoryKernel-backed retriever (Phase 3)
  memory_compressor.py  — Lossy/lossless context compression
  assembler.py          — Dynamic context assembly orchestrator
  injection_logger.py   — Context injection audit trail (Phase 3)
"""

from context.budget_manager import ContextBudgetManager
from context.semantic_retriever import SemanticRetriever
from context.kernel_retriever import KernelRetriever
from context.memory_compressor import MemoryCompressor
from context.assembler import ContextAssembler
from context.injection_logger import InjectionLogger

__all__ = [
    "ContextBudgetManager",
    "SemanticRetriever",
    "KernelRetriever",
    "MemoryCompressor",
    "ContextAssembler",
    "InjectionLogger",
]
