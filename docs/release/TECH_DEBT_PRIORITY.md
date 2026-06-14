# Technical Debt Priority

## Critical

None blocking v0.9.0-rc1, provided the release remains advisory-only.

## High

| Debt | Impact | Recommended Phase |
| --- | --- | --- |
| Shared report snapshot mode | Reduces timestamp churn and release diff noise | v0.9.x stabilization |
| DMN event taxonomy adoption in producers | Improves long-term memory auditability | v0.9.x stabilization |
| Graph health export tied to real graph materialization | Makes graph coverage inspectable | v0.9.x stabilization |

## Medium

| Debt | Impact | Recommended Phase |
| --- | --- | --- |
| Shared stable report writer | Reduces duplicated report code | v0.9.x |
| Report freshness metadata | Clarifies stale evidence | v0.9.x |
| README lifecycle diagram pointer | Improves operator comprehension | v0.9.x |

## Low

| Debt | Impact | Recommended Phase |
| --- | --- | --- |
| Naming cleanup for confidence variants | Reduces conceptual ambiguity | future docs pass |
| Generated artifact inventory automation | Saves manual audit time | future tooling |
