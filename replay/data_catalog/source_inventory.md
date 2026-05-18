# Reality Replay — Source Inventory

> Phase 1A: Historical Data Discovery  
> Generated: 2026-05-14T13:01:00+08:00

## Summary

| Metric | Value |
|--------|-------|
| Total Data Sources | 72 |
| Total Records (JSONL) | 14,178 |
| Global Date Range | 2026-05-11T12:54:11Z → 2026-05-14T05:02:25Z |
| Time Span | ~64 hours |
| Corruption Found | 0 files |
| Empty Sources | 2 (scratchpad, archive) |

---

## 1. JSONL Files (20 sources, 14,178 records)

### Primary Timeline Sources

| # | Path | Records | Date Range | Schema | Confidence | Replay |
|---|------|---------|------------|--------|------------|--------|
| 1 | `memory/dmn.jsonl` | 1,372 | 05-11 12:54 → 05-14 05:01 | dmn_mixed | HIGH | FULL |
| 2 | `logs/actions.jsonl` | 4,136 | 05-11 13:00 → 05-14 05:01 | action_log | HIGH | FULL |
| 3 | `logs/checksums.jsonl` | 8,110 | 05-11 13:00 → 05-14 05:01 | integrity_chain | HIGH | PARTIAL |

### Memory Layer Records

| # | Path | Records | Date Range | Schema | Confidence | Replay |
|---|------|---------|------------|--------|------------|--------|
| 4 | `memory/episodic/records.jsonl` | 328 | 05-11 12:54 → 05-13 15:12 | episodic | HIGH | FULL |
| 5 | `memory/semantic/records.jsonl` | 29 | 05-12 09:01 → 05-13 13:00 | semantic | HIGH | FULL |
| 6 | `memory/procedural/records.jsonl` | 1 | 05-13 12:25 | procedural | HIGH | FULL |
| 7 | `memory/governance/records.jsonl` | 31 | 05-11 21:49 → 05-13 12:31 | governance | HIGH | FULL |
| 8 | `memory/scratchpad/records.jsonl` | 0 | — | scratchpad | HIGH | NONE |
| 9 | `memory/archive/records.jsonl` | 0 | — | archive | HIGH | NONE |
| 10 | `memory/archive/scratchpad_archived.jsonl` | 19 | 05-11 13:36 → 05-11 21:57 | telemetry_archived | MEDIUM | FULL |

### Governance & Guardian Logs

| # | Path | Records | Date Range | Schema | Confidence | Replay |
|---|------|---------|------------|--------|------------|--------|
| 11 | `governance/audit/decisions.jsonl` | 97 | 05-13 13:51 → 05-14 04:03 | governance_decisions | HIGH | FULL |
| 12 | `governance/audit/incidents.jsonl` | 15 | 05-13 13:51 → 05-14 04:03 | governance_incidents | HIGH | FULL |
| 13 | `guardian/approvals.jsonl` | 8 | 05-11 13:00 → 05-11 14:02 | guardian_approvals | HIGH | FULL |
| 14 | `guardian/reflex.jsonl` | 2 | 05-11 21:49 → 05-11 22:14 | guardian_reflex | HIGH | FULL |

### Observability & Cognitive Traces

| # | Path | Records | Date Range | Schema | Confidence | Replay |
|---|------|---------|------------|--------|------------|--------|
| 15 | `observability/decisions/agent_decisions.jsonl` | 1 | 05-13 22:46 | agent_decisions | MEDIUM | PARTIAL |
| 16 | `observability/evolution_audit/audit_2026-05-13.jsonl` | 2 | 05-13 23:08 | evolution_audit | MEDIUM | PARTIAL |
| 17 | `observability/cognitive_trace_v2/lineage_data/lineage.jsonl` | 10 | 05-13 22:34 → 05-13 22:35 | cognitive_lineage | HIGH | FULL |

### Agent & Skill Pipeline

| # | Path | Records | Date Range | Schema | Confidence | Replay |
|---|------|---------|------------|--------|------------|--------|
| 18 | `agents/skillify/pending_registrations.jsonl` | 12 | 05-14 03:15 → 05-14 04:03 | skill_registrations | MEDIUM | PARTIAL |
| 19 | `state/agents/frontend-agent/memory/entries.jsonl` | 5 | 05-13 21:48 | agent_memory | MEDIUM | PARTIAL |
| 20 | `state/agents/frontend-agent/history.jsonl` | 1 | 05-13 21:58 | agent_history | MEDIUM | PARTIAL |

---

## 2. Guardian JSON Files (12 sources)

| # | Path | Type | Generated | Key Data |
|---|------|------|-----------|----------|
| 1 | `guardian/baselines/telemetry_baseline.json` | telemetry_baseline | 05-11 21:55 | 7 metrics, 4 samples |
| 2 | `guardian/baselines/circadian_baseline.json` | circadian_baseline | 05-12 00:29 | 7 metrics, 3 time groups, 21 samples |
| 3 | `guardian/health/health_scores.json` | health_scores | 05-11 22:02 | 20 history entries, 5 subsystems |
| 4 | `guardian/health/memory_pressure_report.json` | memory_pressure | 05-11 22:04 | Docker context, top 10 consumers |
| 5 | `guardian/incidents/patterns.json` | incident_patterns | 05-11 22:15 | 2 incidents, high_memory_usage ×2 |
| 6 | `guardian/incidents/index.json` | incident_index | 05-11 22:15 | 2 incidents, full evidence chains |
| 7 | `guardian/incidents/reflex_confidence_calibration.json` | reflex_calibration | 05-11 22:14 | Scoring artifact detection |
| 8 | `guardian/dreams/latest_dream.json` | guardian_dream | 05-12 08:47 | 2 replays, recalibration candidates |
| 9 | `guardian/simulations/latest_simulation.json` | simulation | 05-12 08:41 | 5 warnings, 3 horizons |
| 10 | `guardian/audits/memory_integrity_audit.json` | integrity_audit | 05-11 23:11 | 11 checks (10 ok, 1 warning) |
| 11 | `guardian/approval_packets/latest_approval_packet.json` | approval_packet | 05-12 08:36 | PREPARE_FOR_APPROVAL |
| 12 | `guardian/recalibration/queue.json` | recalibration_queue | 05-12 08:50 | 2 pending candidates |

---

## 3. State Snapshots (16 sources)

| # | Path | Type | Timestamp |
|---|------|------|-----------|
| 1 | `state/system_state.json` | system_state | 05-14 05:02 |
| 2 | `state/daemon/dmn_tick_status.json` | daemon_status | 05-14 05:02 |
| 3 | `state/somatic_attention_snapshots/attention_snapshot_20260513_230527.json` | attention_snapshot | 05-13 23:05 |
| 4 | `state/topology_snapshots/dependency_baseline.json` | topology_baseline | 05-13 23:04 |
| 5 | `state/topology_snapshots/self_model_20260513_230342.json` | self_model | 05-13 23:03 |
| 6-10 | `state/checkpoints/c11e8536/stage_000-003.json + latest.json` | checkpoint | 05-13 13:45 |
| 11-16 | `state/agents/*/state.json` (×6 agents) | agent_state | 05-13 23:26 |

---

## 4. Policy & Configuration (3 sources)

| # | Path | Type | Content |
|---|------|------|---------|
| 1 | `guardian/policy.yaml` | risk_policy | 3 risk classes, blocked/review keyword lists |
| 2 | `guardian/reflex_policy.yaml` | reflex_policy | 7 anomaly rules, allowed/blocked responses |
| 3 | `guardian/decision_boundary.yaml` | decision_boundary | 4 boundary levels, ~40 route mappings |

---

## 5. Key Findings

### Data Quality
- **Zero corruption** detected across all 72 sources
- **Checksum chain verified** — `logs/checksums.jsonl` provides 8,110 SHA-256 chain entries
- **Chronological ordering** preserved in all timeline files
- **2 empty files** (scratchpad/archive — contents properly archived)

### Temporal Coverage
- **Night 0** (bootstrap): 2026-05-11T12:54:11Z
- **Night 35** (latest DMN tick): 2026-05-14T05:01:25Z
- **Continuous telemetry**: Hourly summaries from 05-12T14:00 through 05-13T13:00
- **Autonomous DMN ticks**: Running through 05-14T05:02

### Notable Event Timeline
1. **05-11 12:54** — Bootstrap initialized
2. **05-11 13:36** — First telemetry capture (sense_local)
3. **05-11 21:49** — First incident: high_memory_usage (99.61%)
4. **05-11 22:14** — Second incident: high_memory_usage (97.69%, scoring artifact)
5. **05-12 00:29** — Circadian baseline established
6. **05-12 08:47** — Dream replay with recalibration suggestions
7. **05-13 12:25** — Cursor-Hermes MCP integration
8. **05-13 22:05** — Multi-agent governance framework online
9. **05-14 03:15** — Skillify pipeline operations begin
10. **05-14 05:02** — Latest autonomous tick

### Schema Diversity
- 24 distinct schema types identified
- Cross-references between sources verified (DMN → incidents → telemetry → baselines)
- Causal lineage chains intact in cognitive_trace_v2
