# Standard checks — integration notes

**English** · [Simplified Chinese](q-standard-contract-integration-20260701.zh-CN.md)

Historical candidate reference, 2026-07-01. This note is not a stable release
declaration; consult the [release guide](../releases/q-workflow-v1.2.md) for
package selection.

## Purpose

Prose standards need checkable gates, clear warning/blocker severity and
regression coverage before they can reliably guide project work.

## Check coverage

The standard checker covers strict expert dispatch cards, dependency blockers,
status-line examples, UTF-8 and mojibake, rule block parsing, and required rule
identifiers. Role, route and task state must remain distinct.

## Validation before adoption

Run the checker on the affected q-workflow skill and its built-in fixtures:

```text
q_standard_check.py --root <q-workflow> --self-test
```

Also run `encoding_guard.py` on changed contract/checker/output files and
`git diff --check`. Inspect failures and recheck after fixes.

## Synchronization and release

Synchronize the intended source, runtime, bootstrap and maintained variant
copies deliberately, then repeat the same checks. Passing local checks does
not authorize publishing or unrelated project migrations. Keep candidate and
stable release status separate.
