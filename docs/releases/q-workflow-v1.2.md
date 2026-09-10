# q-workflow v1.2

## Changes

- Adapt task procedures to the host's available model and tools.
- Reuse approval for the same authorized action; keep diagnosis read-only
  unless the user requests a change.
- Verify publication against the task's selected repository.
- Isolate explicit portfolio-audit roots from personal profile roots.
- Recover interrupted task updates through a hash-checked transaction journal.
- Use focused PDF, audio/video and presentation procedures for focused requests,
  without requiring unrelated extraction or benchmarking work.
- Treat file length and ordinary LF/CRLF mixing as advisory audit findings.
  Missing required references, invalid metadata and bare carriage returns
  still fail validation.
- Provide English and Simplified Chinese README entrypoints.

## Updating

Follow the [English quickstart](../../QUICKSTART.md#updating-later-from-github)
or [Chinese quickstart](../../QUICKSTART.zh-CN.md#后续更新).
Preserve local changes before updating and verify the resume command afterward.

Updating does not automatically remove installed skills outside the current
package. The quickstart explains how to disable an unwanted skill without
deleting customizations.

## Contributor checks

Run these commands from the repository root with Python installed.
The public-install suite also requires Windows PowerShell and creates disposable
test installations under the temporary directory you supply.

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

Authorization tests use mocked services and local fixtures rather than live
provider accounts. Keep generated reports outside the public repository.
