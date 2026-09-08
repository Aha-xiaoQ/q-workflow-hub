# Adaptive Core Research and Compatibility Notes

Research and compatibility record for the v1.2 public scope, 2026-09-08.
This document is not a remote synchronization receipt.

## Evidence and Decisions

| Source | Observed mechanism | Local decision |
|---|---|---|
| [OpenAI Astra guide](https://developers.openai.com/api/docs/guides/latest-model) | Precise instructions matter; clarification, delegation and verification benefit from explicit calibration. | Audit conflicting rules; define scoped autonomy and a test stop condition. Do not infer actual local performance. |
| [OpenAI subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | Native delegation has host-specific capabilities and context controls. | Wrap native tools with bounded ownership; discover actual model choices instead of hardcoded tiers. |
| [OpenAI skills](https://learn.chatgpt.com/docs/build-skills) | Skills are a reusable instruction surface. | Keep the adaptive procedure on demand; preserve required instruction reads. |
| [MCP architecture, versioned 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/architecture) | Hosts own consent and context; capabilities are explicitly negotiated. | Keep authority local; never equate documented API support with an available host tool. Historical architecture reference, not a claim of latest protocol version. |
| [Anthropic effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Composable patterns and environment feedback; complexity has a cost. | Use a pure optional policy probe and behavioral scenarios, not a second orchestration framework. This is historical design guidance, not current product availability. |

Sources were studied for mechanisms only. No third-party code, prompts or
schemas were copied. Provider guidance is not a matched model benchmark.

## Six-Plane Audit

| Plane | Disposition | Change / retained boundary |
|---|---|---|
| Intent and policy | refine | Recognize existing scoped approval and latest cancellation; answer/diagnose remains read-only. |
| State and authority | repair | Registered project release binding replaces one hardcoded repo assumption; task/event/hash/CAS retained. |
| Capability | wrap native | Inherit observed host defaults; no unavailable model/tool/API claims. |
| Execution | simplify | Targeted dirty-scope inspection, explicit pending-operation reconciliation, optional pure advice. |
| Observability | strengthen | Contract tests distinguish pass, stale, denied and pending; no self-certified completion. |
| Evolution | retain evidence gate | Pre/post review, baseline comparison, bounded scenarios; no model-performance or universal stability claim. |

## Compatibility and Limits

- No skill renamed; old commands and task schema remain supported.
- Optional `remote.release_repository` must match the hashed receipt's
  `repository` and a registered profile entry. Missing field retains the old
  workflow-hub default. No implicit multi-repository release coverage.
- No global model, approval, credential, scheduler or application setting changed.
- The policy probe is optional, experimental advice. It cannot authorize actions
  or prove its caller's assertions. Existing safety/domain gates take precedence.
- Task apply now journals recovery state and blocks further shared writers
  until explicit recovery succeeds. Forced process termination is tested;
  power-loss durability and crash atomicity of other writers are not claimed.
- Full agent packet simplification and broad domain-skill rewrites are deferred:
  they require separate compatibility tests, not a global text replacement.
- Rollback only the changed files to their pre-upgrade baseline; do not reset a
  dirty repository or revert unrelated skill improvements.

## Validation Scope

Run the two targeted unittest modules and existing manager self-test. Check
source/bootstrap/runtime parity for touched files, then the strict foundational
suite when claiming installed consistency. Record baseline failures separately.
Real representative-task latency, cost and quality comparisons remain unproven.
