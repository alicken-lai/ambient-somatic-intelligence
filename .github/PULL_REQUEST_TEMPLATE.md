# Pull Request

## Purpose

What problem does this PR solve?

## Scope

What files, systems, and behaviors are affected?

## Risk

What can fail, regress, or become less governable?

Risk level:

- [ ] LOW RISK
- [ ] MEDIUM RISK
- [ ] HIGH RISK

## Rollback

How can this change be reverted, disabled, or safely contained?

## Tests

What tests, checks, or verification evidence support this PR?

## Audit Impact

What logs, traces, decision records, or replay artifacts explain this change?

## Memory Impact

Does this affect memory creation, recall, promotion, retention, deletion, repair, or audit?

## Agent Impact

Does this affect agent behavior, autonomy, routing, tools, or decision boundaries?

## Governance Impact

Does this affect Guardian, governance rules, protected zones, review gates, replay doctrine, or escalation paths?

## Protected Zone Check

- [ ] Does not touch protected zones.
- [ ] Touches protected zones and includes required approval evidence.

Protected zones include `guardian/`, `governance/`, `replay/`, `runtime/`, `kernel/`, `dmn_scoring/`, `memory_promotion/`, and `agent_decision_policy/`.
