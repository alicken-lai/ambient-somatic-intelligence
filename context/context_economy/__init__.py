"""
Context Economy Engine — Phase E of Ambient OS v0.3.

Adds economic reasoning to context management: cost accounting,
token budgeting with priority tiers, retrieval utility scoring,
and information-density optimization via entropy analysis.

Components:
  cost_accountant.py  — Granular per-agent/task/operation cost tracking
  token_economy.py    — System-wide token budget with priority tiers
  retrieval_scorer.py — Utility scoring for retrieval optimization
  entropy_manager.py  — Shannon entropy and redundancy analysis
  economy_reporter.py — Comprehensive economy reporting
"""

from context.context_economy.cost_accountant import ContextCostAccountant, CostRecord, CostSummary
from context.context_economy.token_economy import TokenEconomy, RebalanceProposal, BudgetTier
from context.context_economy.retrieval_scorer import RetrievalUtilityScorer, ScoredRetrieval
from context.context_economy.entropy_manager import ContextEntropyManager, EntropyReport
from context.context_economy.economy_reporter import ContextEconomyReporter, ContextEconomyReport

__all__ = [
    "ContextCostAccountant",
    "CostRecord",
    "CostSummary",
    "TokenEconomy",
    "RebalanceProposal",
    "BudgetTier",
    "RetrievalUtilityScorer",
    "ScoredRetrieval",
    "ContextEntropyManager",
    "EntropyReport",
    "ContextEconomyReporter",
    "ContextEconomyReport",
]
