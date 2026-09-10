# v1.1-beta release candidate

**English** | [Simplified Chinese](RELEASE_CANDIDATE.zh-CN.md)

Local verification results for `v1.1-beta`, recorded on 2026-09-06.

## Scope

Updates q-workflow core and q-skill-creation guidance, plus public-safe cleanup
of the previously bundled pixel skill. Existing beta domain skills retain their
lifecycle labels.

## Verified on 2026-09-06

- Manager self-test: 20 cases pass.
- Pilot self-test: 11 cases pass.
- Release regression suite: 10 tests pass, including first-task registration,
  original-language TODO names and invalid pointer rejection.
- Fresh installation with all three paths explicitly isolated: exit 0.
- No whitespace errors in the targeted diff.
- Two public-install rounds: 202 checks passed, zero failures. Includes real
  installed commands, 17-skill hash parity and fault-injected update rollback.

## Publication and migration precautions

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
