# v1.1-beta release candidate

Status: local release gates passed on 2026-09-06. Remote publication must be
verified separately; this file is not a remote publication receipt.

## Scope

Updates q-workflow core and q-skill-creation guidance from the maintenance
tree, plus public-safe cleanup of the previously bundled pixel skill.
Newer experimental domain work is intentionally excluded. Existing beta
domain skills retain their lifecycle labels; this is not an all-skills upgrade.

## Verified on 2026-09-06

- Independent Code Auditor identified three P2 issues; all were repaired.
- Manager self-test: 20 cases pass.
- Pilot self-test: 11 cases pass.
- Release regression suite: 10 tests pass, including first-task registration,
  original-language TODO names and invalid pointer rejection.
- Fresh installation with all three paths explicitly isolated: exit 0.
- Private machine paths in bundled pixel metadata/evidence were removed.
- No whitespace errors in the targeted diff.
- Two public-install rounds: 202 checks passed, zero failures. Includes real
  installed commands, 17-skill hash parity and fault-injected update rollback.
- Independent Code Auditor re-reviewed the initialization repairs and passed.

## Gates still open

- This release does not update a maintainer's active personal runtime. Porting
  fixes into other maintenance branches is a separate, conflict-reviewed step.
- This distribution starts with a new single root commit. Previous development
  history, tags and author metadata are not included. Before changing an
  existing remote to public, separately remove or resolve its old refs and
  retained objects; replacing the default branch alone is insufficient.
- Changing remote refs and visibility requires repository-owner authorization,
  a private backup and fresh remote-ref checks.

## Reproduce local tests

```powershell
python skills/q-workflow/scripts/test_release_v11_regressions.py
python skills/q-workflow/scripts/q_workflow_manager.py --self-test
python skills/q-workflow/scripts/workflow_pilot.py --self-test
python -B skills/q-workflow/scripts/workflow_stability_suite.py --public-install --fixture-root ./local-state/public-test --rounds 2 --check-only --strict
```

The regression suite uses mocks and isolated fixtures; it does not authorize
tests against a user's live shared focus. Follow the explicit-path installer
options documented by `scripts/init-user.ps1 -Help`.
