# Memory Dataflow Diagram

Phase: 1A Memory Architecture Design Review  
Date: 2026-06-09  
Scope: Current repository findings only.

## Current Observed Dataflow

```mermaid
flowchart TD
    A["Local events: telemetry, CUA observation, agent work, Guardian/reflex events"] --> B["Append durable records"]
    B --> B1["memory/dmn.jsonl"]
    B --> B2["logs/actions.jsonl"]
    B --> B3["guardian/approvals.jsonl and guardian/reflex.jsonl"]
    B --> B4["state/agents/*/memory/entries.jsonl"]

    B1 --> C["scripts/memory_classify.py"]
    C --> D1["memory/episodic/records.jsonl"]
    C --> D2["memory/semantic/records.jsonl"]
    C --> D3["memory/procedural/records.jsonl"]
    C --> D4["memory/governance/records.jsonl"]
    C --> D5["memory/scratchpad/records.jsonl"]
    C --> D6["memory/archive/*.jsonl"]

    D1 --> E["scripts/memory_index.py / memory/index.json"]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E

    D1 --> F["scripts/memory_recall.py lexical/tag/layer recall"]
    D2 --> F
    D3 --> F
    D4 --> F
    D5 --> F
    E --> F

    D1 --> G["memory/memory_kernel.py scored recall/store/decay/TTL"]
    D2 --> G
    D3 --> G
    D4 --> G
    D5 --> G

    B4 --> H["agents/memory.py local recall and ontology promotion gate"]

    F --> I["Recall result: source, source_type, content, tags, timestamp, confidence"]
    G --> J["ScoredRecord: content, layer, score, timestamp, source, tags, decay, access_count, content_hash"]
    H --> K["Agent MemoryEntry: entry_id, layer, confidence, uses, outcomes, contexts"]

    I --> L["Context / operator / agent use"]
    J --> L
    K --> L

    B1 --> M["replay/data_catalog/replay_manifest.json"]
    B2 --> M
    B3 --> M
    D1 --> M
    D2 --> M
    D3 --> M
    D4 --> M
    M --> N["Replay reports and reality replay reconstruction"]

    B3 --> O["scripts/guardian_check.py and Guardian policy artifacts"]
    O --> P["Guardian boundary result: ALLOW / REVIEW_REQUIRED / BLOCK"]
    P --> Q["guardian logs and attention governance bridge"]
```

## Recommended TurboVec Position

```mermaid
flowchart TD
    A["Existing durable memory records"] --> B["Stable record id and content hash"]
    B --> C["Embedding sidecar metadata"]
    C --> D["TurboVec compressed vector index"]
    D --> E["Candidate recall results"]
    E --> F["Governed recall ranking and lexical fallback"]
    F --> G["Recall evidence packet"]
    G --> H["Guardian-inspectable context"]
    G --> I["Replay log / replay pointer"]
```

TurboVec belongs between durable memory records and governed recall ranking. It should produce candidate recalls only.

## Actual Components Used In This Diagram

| Component | Repository Evidence |
| --- | --- |
| DMN append-only memory | `memory/dmn.jsonl`, `memory/schema.json` |
| Layer classification | `scripts/memory_classify.py` |
| Layered memory files | `memory/episodic/records.jsonl`, `memory/semantic/records.jsonl`, `memory/procedural/records.jsonl`, `memory/governance/records.jsonl`, `memory/scratchpad/records.jsonl` |
| Inverted index | `scripts/memory_index.py`, `memory/index.json` |
| Unified lexical recall | `scripts/memory_recall.py`, `memory/recall_schema.json` |
| Kernel recall/store | `memory/memory_kernel.py` |
| Agent-local memory | `agents/memory.py`, `state/agents/*/memory/entries.jsonl` |
| Ontology promotion | `memory/ontology/layer_definition.py`, `memory/ontology/promotion_rules.py`, `agents/memory.py` |
| Replay catalog | `replay/data_catalog/replay_manifest.json`, `replay/data_catalog/source_inventory.md` |
| Guardian classification | `scripts/guardian_check.py`, `guardian/policy.yaml`, `guardian/decision_boundary.yaml` |
| Trace schemas | `observability/trace_schema.py`, `observability/cognitive_trace_v2/causal_trace_schema.py` |

## Missing Dataflow Required Before TurboVec

```mermaid
flowchart TD
    A["Memory record"] --> B["Stable record id"]
    B --> C["Replay pointer"]
    B --> D["Embedding metadata"]
    D --> E["Vector candidate recall"]
    E --> F["Recall evidence packet"]
    F --> G["Guardian inspection"]
    F --> H["Replay reconstruction"]
```

The missing pieces are schema and evidence contracts, not vector implementation.

