"""
Context Engineering Layer — Phase 2 of Ambient OS Architecture Refactor.

Solves context entropy: the problem of limited token budgets, irrelevant retrieval,
and context pollution that degrades agent performance.

Components:
  budget_manager.py    — Token budget allocation and tracking
  semantic_retriever.py — Relevance-scored memory retrieval with layer priority
  memory_compressor.py  — Lossy/lossless context compression
  assembler.py          — Dynamic context assembly orchestrator
"""

from context.budget_manager import ContextBudgetManager
from context.semantic_retriever import SemanticRetriever
from context.memory_compressor import MemoryCompressor
from context.assembler import ContextAssembler

__all__ = [
    "ContextBudgetManager",
    "SemanticRetriever",
    "MemoryCompressor",
    "ContextAssembler",
]
