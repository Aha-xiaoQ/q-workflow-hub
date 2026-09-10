# q-workflow v1.2 — audited public scope

This update keeps the public starter focused on the validated core and its
existing supported companion skills. It does not publish the maintainer's
complete local skill collection or promote unfinished domain experiments.

## What changes

- Inherit actual host model/tool capabilities instead of historical model
  defaults. Keep action authority separate from model capability.
- Avoid repeated approvals for the same authorized action, preserve read-only
  diagnosis, reconcile pending operations, and stop after relevant checks pass.
- Bind release verification to an explicitly registered repository, while
  retaining the workflow-hub default for older task records.
- Make explicit portfolio-audit roots isolated rather than additive to a user's
  profile roots.
- Preserve v1.1 task, authorization-isolation and public-install fixes.
- Recover interrupted task-apply transactions through an explicit, hash-checked
  journal; block shared state writes until unresolved recovery is handled.

## Skill-maintenance follow-up

The maintained PDF, audio/video intake, presentation, code-lifecycle,
skill-creation, roster and workflow skills now distinguish focused tasks from
full extraction, benchmarking and release procedures. Required privacy,
authorization, evidence and independent release-review checks remain in place.

Portfolio size and ordinary LF/CRLF mixing are advisory findings; missing
required references, metadata and bare carriage returns still block validation.
Explicit `--root` values remain isolated from personal profile roots in this
public distribution. `--only-roots` is accepted for compatibility and requires
at least one root. Neither structural scores nor passing tests measure model
intelligence or creative quality.

Legacy installer rollback checks require the intended fault-injection marker
as well as restored files. Their native Windows PowerShell test children use
isolated module-search defaults; this does not change the parent environment
or certify every mixed-host production installer launch.

This follow-up does not restore withdrawn skill packages or add unpublished
specialties. Existing public installation, recovery and authorization fixes
are retained. No release tag is moved by this maintenance commit.

## Withdrawn from the public distribution

The pixel-art, Canvas-game iteration and HTML-interface design skill packages
are removed from the current public tree, registry and advertised install
surface because their remaining validation does not meet this distribution's
scope. Their specialized test fixtures are withdrawn with them; the generic
candidate-before-activation checks remain.

Font design, game production, Arduino release, public-content-review and newer
research-service experiments are not added. Existing local self-use copies are
not deleted by this change. Historical Git revisions and tags are unchanged;
they are not the current supported package. Do not force-reset a local checkout
or overwrite custom skills when updating.

Existing installations may still contain the withdrawn skills: the updater
does not silently delete them. They remain outside current support. To disable
them, preserve custom work and archive only the named folders outside the
runtime and bootstrap skill-discovery directories; keep local self-use sources.
The exact folder names are `q-pixel-art-creation`, `q-game-canvas-iteration`
and `q-html-interface-design`.

## Verification

From the repository root, use the following checks with an existing Python
installation. The public-install suite requires Windows PowerShell and creates
only explicitly scoped disposable installations.

```text
python -B scripts/test_public_portability.py
python -B scripts/test_public_audit_scope.py
python -B skills/q-skill-creation/scripts/test_skill_portfolio_audit.py
python -B skills/q-workflow/scripts/test_installer_environment.py
python -B skills/q-video-intake/scripts/test_public_auth_boundaries.py
python -B skills/q-workflow/scripts/test_release_v11_regressions.py
python -B skills/q-workflow/scripts/test_execution_policy.py
python -B skills/q-workflow/scripts/test_release_repository.py
python -B skills/q-workflow/scripts/test_task_transaction_recovery.py
python -B skills/q-workflow/scripts/workflow_stability_suite.py --public-install --rounds 2 --strict --fixture-root <temporary-directory> --status-output <private-report.json>
```

Mocked authorization tests do not establish live service availability. Policy
tests establish their decision contracts, not a measured model-performance
improvement. Installation and state checks do not certify creative output or
hardware behavior. No unfinished specialty skill is included on that basis.
