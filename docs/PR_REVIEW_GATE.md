# PR Review Gate

## Purpose

Every pull request must show how it preserves ASI governance. Review is mandatory for changes that affect architecture, memory, replayability, Guardian behavior, runtime execution, synchronization, or external action boundaries.

## Required PR Answers

Every PR must answer:

- Purpose: What problem does this solve?
- Scope: What files, systems, and behaviors are affected?
- Risk: What can fail, regress, or become less governable?
- Rollback: How can this be reverted or disabled?
- Test Coverage: What tests, checks, or evidence support the change?
- Auditability: What logs, traces, or records explain the change?
- Memory Impact: Does this affect memory creation, recall, promotion, retention, deletion, or repair?
- Agent Impact: Does this affect agent behavior, autonomy, routing, tools, or decision boundaries?
- Governance Impact: Does this affect Guardian, governance rules, protected zones, review gates, or replay doctrine?

If any answer is unclear, the PR is not ready for approval.

## Risk Levels

### LOW RISK

Low-risk PRs are documentation-only, tests-only, or isolated prototype changes that do not alter runtime behavior, Guardian logic, memory logic, APIs, dependencies, or protected zones.

Required reviewers:

- Author self-review.
- One project reviewer when available.

Required evidence:

- Clear scope.
- Basic verification that files render or tests run when applicable.
- Decision log entry when the change creates or changes governance doctrine.

### MEDIUM RISK

Medium-risk PRs affect experimental zones, adapters, schemas, synchronization plans, test harnesses, or non-production integration paths.

Required reviewers:

- Project reviewer.
- Governance reviewer or owner delegate.

Required evidence:

- Tests or executable checks.
- Rollback plan.
- Memory and audit impact analysis.
- Decision log entry.

### HIGH RISK

High-risk PRs touch protected zones, runtime behavior, Guardian logic, memory scoring, memory promotion, replay gates, production APIs, external action boundaries, or dependency trust boundaries.

Required reviewers:

- Project owner.
- Guardian or safety reviewer.
- Independent verifier when verification claims are made.

Required evidence:

- Explicit approval before merge.
- Objective tests or replay evidence.
- Rollback procedure.
- Decision log entry.
- Guardian safety review.
- No self-certification of promotion, gate PASS, or strategic memory claims.

## Approval Matrix

| Risk Level | Examples | Required Reviewers | Required Evidence | Merge Condition |
| --- | --- | --- | --- | --- |
| LOW RISK | Docs, templates, isolated tests | Author plus one reviewer when available | Scope, verification note | All required PR answers complete |
| MEDIUM RISK | Experimental adapters, schemas, sync plans | Project reviewer and governance reviewer | Tests, rollback, memory/audit impact | Reviewers approve and risks are documented |
| HIGH RISK | Protected zones, Guardian, runtime, replay, DMN logic | Project owner, safety reviewer, independent verifier when needed | Tests, replay evidence, rollback, Guardian review | Explicit approval and no unresolved governance risk |

## Rejection Criteria

Reject or return for revision when a PR:

- Increases capability while reducing control.
- Makes decisions less replayable.
- Treats vector recall as truth.
- Bypasses Guardian or human confirmation boundaries.
- Deletes or hides historical failures, gaps, or incidents.
- Changes protected zones without approval.
- Lacks a rollback path.
- Claims verification without independent evidence.
