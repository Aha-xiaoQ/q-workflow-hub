---
name: q-code-lifecycle
description: Manage code versioning, debug checkpoints, application releases, customer/demo handoffs, and reproducible software packages. Use when Codex edits firmware, scripts, demos, applications, build systems, or test code and needs to preserve useful states without creating noisy history.
---

# Q Code Lifecycle

Use this skill when a project includes code or executable demos. The goal is to preserve important working states during debugging, then produce clean application/release handoffs that another engineer or customer can reproduce.

## Trigger Router

| User intent | Use this skill for |
|:---|:---|
| Debugging or experiments | Preserve useful repro states, logs, probes, and partial fixes without turning them into release deliverables. |
| Application or demo handoff | Clean debug churn, document runnable commands, and prepare reproducible code packages. |
| Release, customer, or colleague sharing | Check status, diffs, validation, version notes, packaging, and residual risk before handoff. |
| Unsure checkpoint cadence | Decide whether to commit locally, defer, or ask before push/publish. |

Pair with `q-workflow` for project routing and durable
memory. This skill owns code lifecycle decisions, not broad project recovery.

## Two-Track Model

Separate code work into two tracks:

- **Debug track**: fast iteration, experiments, instrumentation, temporary probes, and partial fixes.
- **Application track**: reviewed, documented, reproducible code intended for reuse, demo, customer sharing, or release.

Do not let debug churn pollute application deliverables. Do not lose valuable debug states that may be hard to recreate.

## Debug Track

During debugging:

1. Check `git status --short --branch` before edits.
2. Keep changes scoped to the active hypothesis when possible.
3. Preserve important states as lightweight checkpoints when any of these happens:
   - a bug is reproduced clearly
   - a partial workaround works
   - a hardware/demo state is known good
   - a risky refactor is about to start
   - the user may need to return to this behavior later
4. Record only high-signal checkpoint notes in `TASKS.md` or `PROJECT_STATE.md`.
5. Commit debug checkpoints when they are useful recovery points. Use clear messages such as:
   - `Checkpoint UART boot log capture`
   - `Checkpoint stable MPPT scan prototype`
   - `Reproduce ADC timing issue`
6. Remove or isolate temporary logs, dumps, instrumentation, and local-only settings before application release.

Prefer small meaningful checkpoints over one large ambiguous commit. Avoid committing every tiny failed attempt.

## Application Track

Before treating code as usable application/demo code:

1. Remove debug-only instrumentation unless explicitly documented as a diagnostic feature.
2. Verify build/run/test commands from a clean checkout where feasible.
3. Document hardware, wiring, board revision, firmware image, toolchain, dependencies, and input data needed to reproduce.
4. Add or update README/demo instructions so another engineer can run it without chat history.
5. Include expected output, screenshots, logs, or measurement checkpoints when useful.
6. Mark limitations, known issues, and unsupported configurations.
7. Tag or clearly commit the release/demo state when it matters.

## Conditional Release Checks

- For a skill/workflow or reusable-package install, mirror, commit, push, release or readiness claim, read `references/source-runtime-consistency.md` before making the claim. A local checkpoint needs only its scoped diff; local install and remote claims retain their different evidence requirements.

## Versioning Rules

- Use Git commits as the primary durable recovery mechanism.
- Use branches only when parallel work or risky experiments need separation.
- Use tags for externally shared demos, customer handoffs, or milestone snapshots.
- Keep generated binaries out of Git unless they are small, intentionally shared deliverables, or needed for reproduction.
- Keep credentials, activation/license keys, private keys, and machine-local secrets out of Git. Preserve required redistributable LICENSE and NOTICE files.
- When large artifacts are required, document their source path and regeneration command.

## Handoff Package Expectations

For code that may be shared or handed off, include enough material to reproduce:

- Project purpose and supported hardware/software versions.
- Exact build commands and required tools.
- Flash/run/debug steps.
- Hardware connection diagram or table when relevant.
- Required PPT, report, dataset, config, or calibration files.
- Validation steps and expected results.
- Troubleshooting notes for common failure modes.

Use `ENVIRONMENT.md` for machine and tool setup, and project README files for user-facing reproduction steps.

## Working With q-workflow

When this skill is used inside a q-workflow-managed project:

- Update `PROJECT_STATE.md` after meaningful code progress.
- Update `TASKS.md` with debug checkpoints worth preserving.
- Update `DECISIONS.md` for architectural or release-policy decisions.
- Update `ENVIRONMENT.md` for toolchain, dependency, hardware, or reproduction changes.
- Preserve a scoped local checkpoint at meaningful boundaries. Push only within
  explicit authorization for the current target and candidate, following
  q-workflow's sync-and-push policy; completion alone is not push authorization.

## References

Read `references/debug-release.md` for a compact checklist when a debugging session transitions into a shareable demo or application release.
