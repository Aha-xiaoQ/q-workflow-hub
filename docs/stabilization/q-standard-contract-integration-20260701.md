# Q Standard Contract Integration Note

Date: 2026-07-01
Trace: q-standard-stabilization-20260701
Status: local candidate passed

## Scope

This loop addressed a workflow-level failure mode: standards existed as prose but were not reliably enforced as hard gates, expert dispatch cards, warning/blocker semantics, or regression tests.

## Accepted Findings

- Doc Architect (文构): no blocker; fixed lifecycle/token ambiguity by keeping the contract at candidate status and making real rules machine-checkable.
- Code Auditor (码鉴): initial blocker that `q_standard_check.py` was too shallow; fixed with strict expert-card parsing, dependency blocker handling, status-line example scanning, UTF-8/mojibake checks, real rule block parsing, and required real rule IDs.
- Code Auditor (码鉴) rereview: blocker closed; `blocking_stabilization: no`.

## Validation

- PASS: `q_standard_check.py --root <q-workflow> --self-test`
- PASS: `encoding_guard.py` on changed contract/checker/output files
- PASS: `git diff --check`

## Protocol Findings

- Initial Doc Architect report retained `platform_agent: explorer/pending`; main-agent had shown run instance in chat but had not sent IDENTITY-UPDATE to that subagent. This is recorded as a protocol defect.
- Later Code Auditor runs received IDENTITY-UPDATE and returned exact platform handles.

## Frozen Scopes

- GMPPT directory migration remains frozen.
- PPT-specific validator severity refactor remains frozen.
- GitHub/Bitbucket push remains approval-gated.
- Project-structure standard remains candidate, not stable.

## Next Gate

Before using this as a stable workflow release, sync source/runtime/bootstrap/company surfaces deliberately and run the same `q-standard-check` gate after synchronization.
