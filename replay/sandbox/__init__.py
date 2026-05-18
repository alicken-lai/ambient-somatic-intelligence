"""Reality Replay Sandbox — Phase 1B.

Isolated replay environment that reprocesses historical operational
data through the ontology pipeline without modifying production data.

Quick start::

    from replay.sandbox import ReplayConfig, ReplayRunner
    config = ReplayConfig(auto_approve_for_replay=True)
    runner = ReplayRunner(config, workspace_root=".")
    result = runner.run(episodes_path="memory/somatic/episodes.jsonl")
"""

from .replay_config import ReplayConfig
from .replay_decay_engine import ReplayDecayEngine
from .replay_memory_store import ReplayMemoryStore
from .replay_observability import ReplayObservability
from .replay_promotion_engine import ReplayPromotionEngine
from .replay_runner import ReplayRunResult, ReplayRunner
from .replay_verifier import ReplayVerifier

__all__ = [
    "ReplayConfig",
    "ReplayDecayEngine",
    "ReplayMemoryStore",
    "ReplayObservability",
    "ReplayPromotionEngine",
    "ReplayRunResult",
    "ReplayRunner",
    "ReplayVerifier",
]
