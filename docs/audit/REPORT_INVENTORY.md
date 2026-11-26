# Report Inventory

## Generated Reports

| Report | Kernel | Purpose | Consumer | Retention Value |
| --- | --- | --- | --- | --- |
| `deliberation_quality_report.md` | Evaluation | Quality scoring | operator/audit | medium |
| `deliberation_learning_report.md` | Routing | Routing learning | routing strategy | medium |
| `deliberation_roi_report.md/json` | Routing/ROI | ROI evidence | strategy/audit | high |
| `deliberation_strategy_report.md/json` | Strategy | Mode explanation | operator | medium |
| `playbook_report.md/json` | Skills/Playbooks | Playbook inventory | verification/identity | high |
| `skill_report.md/json` | Skills | Skill inventory | identity/reality | high |
| `failure_learning_report.md/json` | Learning | Failure modes | governance/audit | high |
| `evidence_report.md/json` | Verification | Evidence score | acquisition/calibration | high |
| `claim_report.md/json` | Verification | Claims | evidence audit | high |
| `verification_report.md/json` | Verification | Verification coverage | audit | high |
| `contradiction_report.md/json` | Verification | Contradictions | audit | high |
| `acquisition_report.md/json` | Acquisition | Evidence acquisition | calibration | high |
| `evidence_quality_report.md/json` | Acquisition | Source/evidence quality | calibration | high |
| `knowledge_index_report.md/json` | Acquisition | Indexed knowledge | recall/audit | medium |
| `knowledge_health_report.md/json` | Calibration | Knowledge health | reality | high |
| `trust_report.md/json` | Calibration | Trust rankings | reality/identity | high |
| `drift_report.md/json` | Calibration | Knowledge drift | identity | high |
| `reality_alignment_report.md/json` | Reality | Reality score/challenges | identity/audit | high |
| `diversity_report.md/json` | Reality | Diversity/echo risk | audit | high |
| `institutional_fitness_report.md/json` | Reality | Fitness | identity/audit | high |
| `identity_report.md/json` | Identity | Identity/health | audit | high |
| `continuity_report.md/json` | Identity | Stability/change | audit | high |
| `life_history_report.md/json` | Identity | Institutional biography | audit/operator | high |

## Duplicates

- Markdown and JSON pairs are useful but should be treated as paired artifacts.
- `trust_registry.json` and `trust_report.json` overlap but serve different purposes.
- `belief_registry.json` and `identity_report.json` overlap in belief state but not identity profile.

## Obsolete Reports

No obsolete reports identified. Some may be rebuildable and should not be treated as canonical policy.

## Missing Reports

- Persistent graph coverage report
- Report freshness/staleness report
- DMN event taxonomy report
