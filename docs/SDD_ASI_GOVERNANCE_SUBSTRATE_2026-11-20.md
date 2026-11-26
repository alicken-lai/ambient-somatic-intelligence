# Software Design Document: ASI as Governance Substrate

**Version:** 1.0.0  
**Date:** 2026-11-20  
**Status:** ACTIVE  
**Purpose:** Prevent scope drift, define product boundaries, guide P4-P7 execution

---

## 1. Executive Summary

### 1.1 Problem Statement

Over 5 months (2026-06-15 to 2026-11-20):
- **Product core changes:** 0 lines
- **Governance infrastructure added:** 32,767 lines
- **P0-P8 evolution plan execution:** <5%
- **Root cause:** Goal conflation — environment migration gates (G0-G6) wrongly applied to product release

### 1.2 Core Positioning

**ASI is NOT competing with frontier models on general reasoning, execution, or computer use.**

**ASI IS a model-external governance substrate providing:**
- Somatic sensing (environment awareness)
- DMN memory (institutional continuity)
- Guardian authorization (fail-closed action control)
- Provenance & replay (audit trail)
- Multi-model adapter layer (provider neutrality)

### 1.3 Scope Boundaries

| In Scope (Product) | Out of Scope (Leave to Models) |
|-------------------|--------------------------------|
| Authorization envelope design | General task planning |
| Action provenance & replay | Code execution runtime details |
| Multi-model adapter interface | Browser/computer-use primitives |
| Guardian policy framework | Context-window compression |
| DMN append governance | Specialist agent orchestration |
| Reality alignment metrics | Frontier reasoning capabilities |

### 1.4 Anti-Drift Checkpoints

Every new work item must pass:
1. **Product vs Environment test:** Is this core product capability or operator environment tooling?
2. **Boundary test:** Does this compete with frontier model capabilities, or govern them?
3. **Blocker test:** Does current product release actually depend on this?
4. **P-phase alignment:** Which P-phase does this serve? If none, defer or reject.

---

## 2. Architecture Vision

### 2.1 Layered Model

```
┌─────────────────────────────────────────────────────┐
│ User Intent / Environment Telemetry                 │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Somatic Sensing + Attention Kernel                  │
│ (what changed? what matters? weak signals)          │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ DMN Memory Recall (institutional context)           │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Frontier Model Adapter Layer ◄─ REPLACEABLE        │
│ (Astra / Claude / Gemini / Local)                   │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Proposed Action Envelope                            │
│ {intent, scope, tool, side_effect_class,            │
│  reversibility, authorization_ref}                  │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Guardian Authorization ◄─ MODEL-EXTERNAL            │
│ ALLOW / REVIEW / BLOCK                              │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Tool Execution / Result Evidence Envelope           │
│ {who, when, what, outcome, error, cost}             │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Append-only Provenance + Replay Store               │
└─────────────────────────────────────────────────────┘
```

### 2.2 Core Principles

1. **Model-external authorization:** Guardian decisions cannot be bypassed by model reasoning or output
2. **Provider neutrality:** Switching from Claude to Astra or Gemini requires zero Guardian policy changes
3. **Replay-first:** Every material action must be reconstructable from evidence
4. **Fail-closed:** Unknown/missing authorization = BLOCK
5. **Append-only memory:** No silent deletion of historical gaps or failed gates

---

## 3. Product Phases (P0-P8)

### 3.1 Phase Priority Matrix

| Phase | Priority | Rationale | Blocker for |
|-------|----------|-----------|-------------|
| **P0** | ✅ DONE | SSOT alignment completed 2026-11-20 | All |
| **P3** | ✅ DONE | PPM blockers resolved | P5 evidence quality |
| **P4** | 🔴 CRITICAL | Core architecture shift to governance substrate | P7 pilot, product differentiation |
| **P7** | 🔴 CRITICAL | Validation of P4 with real frontier model | Product viability proof |
| **P1** | 🟡 MEDIUM | Hermes update (staging ready, not blocking product) | P2 compatibility |
| **P2** | 🟡 MEDIUM | Bridge compatibility (blocked by Guardian policy) | P1 cutover safety |
| **P5** | 🟡 MEDIUM | Evidence integrity (remove hardcoded PASS) | Quality claims |
| **P8** | 🟡 LOW | Documentation reconciliation | External clarity |
| **P6** | 🟢 DEFERRED | Reality debt (insufficient evidence, not actionable) | Future promotion |

### 3.2 P4: Boundary Refactor (CRITICAL PATH)

**Objective:** Shift ASI from "general agent orchestrator" to "model-external authorization layer"

**Deliverables:**
1. **Capability Registry** (`asi/capabilities.py`)
   - Enumerate all material actions (file write, git commit, external API, etc.)
   - Define authorization requirements per capability
   - Map tools to capabilities (1:N relationship)

2. **Provider-Neutral Model Adapter** (`asi/adapters/`)
   ```python
   class ModelAdapter(Protocol):
       def propose_action(self, context: Context) -> ActionEnvelope: ...
       def explain_reasoning(self) -> str: ...  # NOT authorization evidence
   ```

3. **Action Envelope Schema** (`asi/schemas/action_envelope.py`)
   ```python
   @dataclass
   class ActionEnvelope:
       intent: str                    # human-readable goal
       scope: ActionScope             # filesystem, network, state, etc.
       tool: str                      # specific tool name
       arguments: dict                # tool-specific args
       side_effect_class: SideEffect  # read_only, reversible, destructive
       reversibility: Reversibility   # automatic, manual, irreversible
       authorization_ref: str         # Guardian policy rule matched
       proposed_by: str               # model id + version
       timestamp: datetime
   ```

4. **Result Evidence Envelope** (`asi/schemas/result_envelope.py`)
   ```python
   @dataclass
   class ResultEnvelope:
       action_ref: str                # links to ActionEnvelope
       outcome: Outcome               # success, failure, partial, timeout
       actual_changes: list[Change]   # file diffs, API responses, etc.
       error: Optional[Exception]
       cost: ResourceCost             # tokens, time, API calls
       replay_pointer: str            # immutable reference for audit
       verified_by: Optional[str]     # independent verifier id
       timestamp: datetime
   ```

5. **Bypass Prevention Tests** (`tests/test_guardian_bypass.py`)
   - Model output cannot directly invoke tools
   - Reasoning/explanation text is not treated as authorization evidence
   - Mid-turn steering preserves full trajectory
   - Action envelope schema violations cause hard failure

**Current Status:**
- Code exists in P4 implementation proposals
- Appeal submitted after finding 4 bypass vulnerabilities
- Awaiting independent verification (cannot self-approve)

**Acceptance Criteria:**
- ✅ Model adapter is swappable (Claude ↔ Astra ↔ Gemini) without Guardian policy changes
- ✅ All material actions go through Guardian (no bypass in threat model test cases)
- ✅ Action/result envelopes are replay-compatible
- ✅ Independent verifier confirms no regressions

### 3.3 P7: Astra Pilot (VALIDATION)

**Objective:** Prove P4 architecture with GPT-6 Astra as first replaceable adapter

**Scope:**
- **Environment:** Sandbox/canary only (NOT production)
- **Model:** OpenAI GPT-6 Astra via Responses API (async tool calling support)
- **Test Scenarios:**
  1. Multi-file refactoring with rollback
  2. External API integration with credential protection
  3. Mid-turn user correction (trajectory preservation)
  4. Unauthorized action attempt (Guardian BLOCK verification)
  5. Long-horizon task with cost tracking

**Metrics:**
| Metric | Target | Rationale |
|--------|--------|-----------|
| Material action bypass rate | 0% | Guardian is non-negotiable |
| Replay success rate | 100% | Audit integrity requirement |
| Human interruption latency | <3s | Safety requirement |
| Unauthorized action attempts | >0 observed, 100% blocked | Proves Guardian works |
| Cost tracking accuracy | 100% | Institutional accountability |

**Non-Goals:**
- Proving Astra is "better" than Claude
- Production deployment of Astra
- Replacing Hermes Agent entirely
- Benchmarking general reasoning capabilities

**Completion Criteria:**
- All 5 test scenarios executed with evidence
- Metrics report generated and reviewed
- Bypass prevention validated by independent reviewer
- Rollback to Claude-only mode tested and working

### 3.4 P1: Hermes Update (INFRASTRUCTURE)

**Objective:** Update Hermes Agent from v0.16.0 to v0.21.2

**Why P1 is NOT blocking product release:**
- v0.9.0-rc1 released 2026-06-15 with v0.16.0
- v0.21.2 fixes multi-writer/WAL issues (operational improvement, not product capability)
- Staging installation already complete at `.staging/hermes-0.21.2-939e45c`
- G0-G6 gates are **environment migration safety gates**, not product acceptance criteria

**G0-G6 Gate Structure:**
```
P1 (Hermes Update)
├── G0: Inventory (唯讀盤點)
├── G1: Source verification (來源驗證)
├── G2: Backup & restore rehearsal (備份演練) ◄── CURRENT BLOCKER
├── G3: Staging install (隔離安裝) ✅ DONE
├── G4: Isolated migration (隔離遷移)
├── G5: Active cutover (正式切換)
└── G6: Independent verification (獨立驗證)
```

**G2 Blocker Resolution:**
- Previous failures: cryptography version mismatch, live-writer race condition
- Need: One clean ACL witness verification run
- NOT a product development blocker — this is operator environment tooling

**P1 Execution Rule:**
- G0-G6 work is operator-initiated maintenance, not feature development
- Product phases (P4, P7) proceed independently
- If G2-G6 remain blocked, document limitation and release v0.9.x with v0.16.0

---

## 4. Scope Control Mechanisms

### 4.1 Decision Template

Every proposed work item must complete this form:

```markdown
## Work Item: [Name]

### Classification
- [ ] Product core (ASI governance capabilities)
- [ ] Product infrastructure (testing, CI, docs)
- [ ] Environment tooling (operator workflow, Hermes update)
- [ ] Governance infrastructure (audit, compliance, gates)

### P-Phase Alignment
Which phase does this serve? [P0/P1/P2/P3/P4/P5/P6/P7/P8 or NONE]

If NONE: Why is this needed now?

### Boundary Check
Does this compete with or replicate frontier model capabilities?
- [ ] YES → REJECT (let models handle it)
- [ ] NO → Proceed

### Blocker Test
Is current product release actually blocked on this?
- [ ] YES → What evidence proves the block?
- [ ] NO → Can this be deferred to post-release?

### Scope Limit
Maximum lines of code: [estimate]
Maximum new files: [estimate]
Expected completion: [days, not months]

If estimate > 1000 LOC or > 2 weeks: Break into smaller units or defer.
```

### 4.2 Anti-Pattern Detection

**Pattern 1: Infinite Governance Expansion**
- Symptom: Adding gates, compliance checks, audit layers without clear product value
- Test: Does this enable a user-visible capability or prevent a known operational failure?
- Action: If NO to both, reject or defer

**Pattern 2: Environment Work Disguised as Product Work**
- Symptom: Proposing "necessary foundation" that doesn't connect to P4-P7 deliverables
- Test: Can product demo proceed without this?
- Action: If YES, move to separate environment backlog

**Pattern 3: Competing with Frontier Models**
- Symptom: Building context compression, smart retry, or task decomposition logic
- Test: Will Astra/Claude/Gemini provide this in 6 months?
- Action: If YES, use adapter pattern instead of reimplementation

**Pattern 4: Retroactive Criteria Inflation**
- Symptom: Applying new gates to already-released versions (e.g., G0-G6 to v0.9.0-rc1)
- Test: Was this criterion documented before the release decision?
- Action: If NO, it applies to future releases only

### 4.3 Weekly Scope Review

Every Friday 17:00 Asia/Taipei:
1. List all active work items
2. Verify each against Decision Template
3. Identify scope drift candidates
4. Close or defer items failing boundary tests
5. Update P-phase progress metrics

---

## 5. Implementation Roadmap

### 5.1 Immediate Actions (Week 1-2)

1. **Finalize P4 verification** (CRITICAL)
   - Independent reviewer examines appeal implementation
   - If PASS: Merge to main
   - If FAIL: Specific fix list, no incremental patches

2. **P7 pilot planning** (CRITICAL)
   - Define 5 test scenarios in detail
   - Set up sandbox environment
   - Document Astra API integration requirements
   - Create metrics collection harness

3. **Scope review process** (ANTI-DRIFT)
   - Template all current work items
   - Close non-aligned items
   - Set up weekly review calendar

### 5.2 Phase Execution Order

```
Week 1-2:  P4 verification → merge or fix
Week 3-4:  P7 pilot setup + scenario 1-2
Week 5-6:  P7 scenario 3-5 + metrics report
Week 7:    P7 independent review
Week 8:    P8 documentation reconciliation
Week 9+:   P1/P2 if operationally needed, P5 evidence cleanup
```

### 5.3 P1/G2-G6 Handling

**Option A: Defer to post-release**
- Ship v0.9.1 with current v0.16.0 Hermes
- Document v0.21.2 as future operational improvement
- Operator tackles G2-G6 on their own schedule

**Option B: Resolve in parallel**
- Product work (P4/P7) proceeds on main branch
- Environment work (G2-G6) proceeds on separate branch/repo
- Zero cross-dependency: product demo never waits for Hermes update

**Recommended:** Option A (defer) unless operator explicitly prioritizes G2 resolution

---

## 6. Success Metrics

### 6.1 Product Metrics

| Metric | Baseline (2026-11-20) | Target (2027-01-20) |
|--------|----------------------|---------------------|
| P4 implementation status | 90% (awaiting verification) | 100% merged |
| P7 pilot completion | 0% | 100% with report |
| Model adapters supported | 1 (Claude) | 2 (Claude + Astra) |
| Bypass vulnerabilities in production | Unknown | 0 confirmed |
| Product core LOC | ~15,000 (est.) | <20,000 |
| Governance infrastructure LOC | 32,767 | <35,000 (growth capped) |

### 6.2 Anti-Drift Metrics

| Metric | Target |
|--------|--------|
| Work items rejected for scope misalignment | >30% (proves filter is working) |
| Average lines per merged PR | <500 (surgical changes) |
| P-phase unaligned work merged | 0 |
| Retroactive criteria applied to released versions | 0 |
| Governance infrastructure growth rate | <10% per quarter |

### 6.3 Operational Metrics (P1 only)

| Metric | Current | Target |
|--------|---------|--------|
| Hermes version | v0.16.0 | v0.21.2 |
| G2 gate status | BLOCKED | PASS |
| Staging installation | Complete | Promoted to active |
| Rollback capability | Untested | Verified |

**Note:** These are operator environment metrics, NOT product release criteria.

---

## 7. Governance

### 7.1 Document Authority

This SDD is SSOT (Single Source of Truth) for:
- Product scope boundaries
- P-phase priorities
- Scope control mechanisms
- Weekly review process

Conflicts between this SDD and other documents:
1. This SDD supersedes task proposals, implementation plans, and verbal agreements
2. Protocol gates (G0-G6) remain authoritative for P1 only
3. P4-P8 follow this SDD; P1-P2 follow G0-G6 protocol
4. User/operator can override this SDD at any time with explicit instruction

### 7.2 Change Control

SDD changes require:
- Explicit user approval
- Version increment (semver)
- Changelog entry with rationale
- Re-verification of active work items against new boundaries

### 7.3 Audit Trail

All scope decisions append to: `docs/audit/SCOPE_DECISIONS_2026.md`

Format:
```markdown
### [YYYY-MM-DD] Work Item: [Name]
**Decision:** APPROVED / REJECTED / DEFERRED
**Rationale:** [Decision Template results]
**P-Phase:** [P0-P8 or NONE]
**Decided by:** [user/operator/agent]
```

---

## 8. Risk Register

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| P4 verification fails again | MEDIUM | HIGH | Alternative architecture review, external consultant |
| Astra API changes before P7 | MEDIUM | MEDIUM | Version pinning, adapter abstraction allows pivot |
| Guardian bypass found in production | LOW | CRITICAL | Red team testing, independent security review |
| Model reasoning used as authorization | MEDIUM | HIGH | Schema validation, automated bypass detection |

### 8.2 Organizational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Scope drift resumes | HIGH | HIGH | Weekly review, Decision Template enforcement |
| P1/G2-G6 blocks product work | MEDIUM | MEDIUM | Explicit decoupling, Option A (defer) |
| Infinite governance expansion | MEDIUM | HIGH | LOC growth cap, anti-pattern detection |
| User frustration with slow progress | MEDIUM | HIGH | Focus on P4/P7 (visible product value), defer infrastructure |

### 8.3 Market Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Frontier models add native governance | MEDIUM | HIGH | ASI's institutional memory/provenance remain differentiators |
| Authorization substrate becomes commodity | LOW | MEDIUM | Deep integration with somatic sensing + DMN |
| Competition replicates action envelope pattern | MEDIUM | LOW | Execution speed, not novelty, wins |

---

## 9. Appendices

### 9.1 Glossary

- **Action Envelope:** Structured representation of a proposed material action before Guardian authorization
- **Material Action:** Any operation with side effects (writes, API calls, state changes)
- **Model-External:** Logic/policy that exists outside the frontier model and cannot be influenced by its reasoning
- **P-Phase:** One of P0-P8 evolution phases defined in 2026-09-13 plan
- **G-Gate:** One of G0-G6 environment migration safety gates (P1 subprocess)
- **Scope Drift:** Expanding project scope without corresponding product value (anti-pattern)
- **Governance Substrate:** ASI's core positioning as authorization/provenance layer, not execution engine

### 9.2 References

- [ASI Evolution Plan 2026-09-13](../proposals/ASI_EVOLUTION_AND_HERMES_UPDATE_PLAN_2026-09-13.md)
- [Hermes-ASI v0.9 Architecture](../architecture/HERMES_ASI_V09.md)
- [v0.9.0-rc1 Release Decision](../release/RELEASE_DECISION.md)
- [P4 Implementation Proposal](../proposals/ASI_P4_PROVIDER_NEUTRAL_ACTION_GOVERNANCE_IMPLEMENTATION.md)
- [P4 Appeal Implementation](../proposals/ASI_P4_PROVIDER_NEUTRAL_ACTION_GOVERNANCE_APPEAL_IMPLEMENTATION.md)
- [ASI Update Verification Protocol](../proposals/ASI_UPDATE_VERIFICATION_PROTOCOL_2026-10-25_CANDIDATE.md)

### 9.3 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-11-20 | Codex Agent | Initial SDD creation to prevent scope drift |

---

**Document Status:** ACTIVE — use this as SSOT for all product development decisions.

**Next Review:** 2026-11-27 (weekly scope review)

**Owner:** User / Operator

**Maintained by:** ASI Project Team
