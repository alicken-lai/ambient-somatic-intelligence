"""Mine reusable patterns from deliberation evidence."""

from __future__ import annotations

from collections import Counter
from typing import Any


def mine_patterns(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    child_combinations: Counter[str] = Counter()
    verification_sequences: Counter[str] = Counter()
    routing_paths: Counter[str] = Counter()
    synthesis_strategies: Counter[str] = Counter()
    for result in results:
        winner = str(result.get("winner", "unknown"))
        category = str(result.get("category", "unknown"))
        routing_paths[f"{category}->{winner}"] += 1
        if winner == "single":
            child_combinations["primary_provider_only"] += 1
        elif winner == "light":
            child_combinations["engineering+risk"] += 1
        else:
            child_combinations["engineering+risk+verification"] += 1
        verification_sequences["claim_status_verifier"] += 1
        synthesis_strategies["preserve_uncertainty"] += 1
    return {
        "child_combinations": _rank(child_combinations),
        "verification_sequences": _rank(verification_sequences),
        "routing_paths": _rank(routing_paths),
        "synthesis_strategies": _rank(synthesis_strategies),
    }


def _rank(counter: Counter[str]) -> list[dict[str, Any]]:
    return [{"pattern": key, "count": count} for key, count in counter.most_common()]
