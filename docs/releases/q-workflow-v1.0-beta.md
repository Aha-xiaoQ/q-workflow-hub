# q-workflow v1.0-beta

**English** | [Simplified Chinese](q-workflow-v1.0-beta.zh-CN.md)

`v1.0-beta` is the first public beta of the recovery-first q-workflow kernel.
Its SemVer-compatible prerelease identity is `1.0.0-beta`; its display tag is
`v1.0-beta`.

## Promotion links

- [Repository](https://github.com/Aha-xiaoQ/q-workflow-hub)
- [Versioned source](https://github.com/Aha-xiaoQ/q-workflow-hub/tree/v1.0-beta)
- [English quickstart](../../QUICKSTART.md)
- [Simplified Chinese quickstart](../../QUICKSTART.zh-CN.md)
- [Changelog](../../CHANGELOG.md)
- [Issue tracker](https://github.com/Aha-xiaoQ/q-workflow-hub/issues)

## Included scope

- `skills/q-workflow`: manager CLI, task-state and event contracts, surface
  registry, runtime manifest, recovery/output gates, validation and stability
  tooling.
- `skills/q-agent-roster`: the handoff, validation-scenario, and adaptive child
  model-routing surfaces directly exercised by the workflow gates.
- `skills/q-skill-creation/scripts/skill_portfolio_audit.py`: the profile-aware
  portfolio probe used by full doctor.
- `scripts/sync-workflow-bootstrap.ps1`: registry-validated source-to-bootstrap
  and optional runtime synchronization.

## What changed

- `q_workflow_manager.py` provides one read-only default entry for `status`,
  `doctor`, `registry`, `surfaces`, and task discovery/validation.
- Material task mutation uses a reviewable plan/apply transaction with explicit
  confirmation, compare-and-swap hashes, a shared operating-system lock,
  atomic replacement, rollback, readback checks, and receipts.
- `ACTIVE_WORK.md` is a focus projection rather than the only task database;
  task records and JSONL events allow independent `task_id` / `trace_id`
  validation.
- A content-addressed surface registry controls source, bootstrap, runtime, and
  personal-source expectations. Sync validates the registry before staging.
- Operational evidence is intentionally small: status, hashes, `elapsed_ms`,
  stable `failure_class`, and artifact paths. Prompts, credentials, and private
  artifact bodies are not default telemetry.

## Install or pin the beta

Fresh clone:

```powershell
git clone --branch v1.0-beta --depth 1 https://github.com/Aha-xiaoQ/q-workflow-hub.git
```

Existing clone:

```powershell
git fetch --tags origin
git switch --detach v1.0-beta
```

The tag is immutable. A detached tag checkout does not use `git pull`; fetch
tags and switch explicitly to a newer reviewed tag when one is published.

After selecting the beta source, follow the [English quickstart](../../QUICKSTART.md) or
[Simplified Chinese quickstart](../../QUICKSTART.zh-CN.md). Existing users can run the
documented `scripts/sync-workflow-bootstrap.ps1` path to refresh a private
bootstrap and optional runtime installation.

## Compatibility

- Existing Markdown state remains readable.
- `RECOVERY_POINTER v1` remains a flattened compatibility view.
- `sync_state` is a derived legacy alias; work, integrity, and release remain
  independent axes in registered task records.
- Unknown future major schemas fail closed instead of being guessed.
- The new manager commands are additive; task writes still require an explicit
  plan followed by apply with `--yes`.

## Validation evidence

Local verification completed two strict full-doctor rounds with 76 checks and
zero failures. Checks included:

- registry validation and strict core-surface inspection;
- manager, task-state, lifecycle, q-standard, and output-preflight self-tests;
- the two-round strict stability suite and two-round full doctor;
- public/private scan, UTF-8 guard, Python compilation, and `git diff --check`.

## Known limitations

- A forced process termination between multi-file switches can leave a partial
  transaction because a durable write-ahead journal is not implemented yet.
- The release guarantee covers the five registered core surfaces. Flagship and
  lab skills remain separately versioned candidates unless their own gates say
  otherwise.
- Remote freshness is proven only by a successful fetch/push/readback cycle;
  a local tag or cached tracking reference is not sufficient.

## Recovery and rollback

Keep private state outside this public starter. To inspect the public starter
before this beta without rewriting a working branch, use:

```powershell
git switch --detach 74096b83cf75ffec64dac4e07f35c701993efa10
```

Return to the beta with `git switch --detach v1.0-beta`. Do not force-reset an
unknown or dirty working tree.
