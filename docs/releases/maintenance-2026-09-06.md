# Selective skill maintenance — 2026-09-06

Historical note: the [v1.2 public scope](q-workflow-v1.2.md) supersedes the
HTML and pixel package inclusion below. Those packages are withdrawn from the
current distribution pending validation; historical revisions are unchanged.

This branch update follows `v1.1-beta`; it does not replace or move that tag.
The workflow core remains unchanged from the public release.

## Included

- HTML interface design: visual maturity/finish review and an experimental
  interaction-state craft reference; product-derived geometry and type choices.
- Pixel creation: whole-contour, colour-first cleanup with protected silhouette
  anchors; native avatar authority, consumer-specific derivatives, and archive rules.
- Video intake: explicit multipart page selection, authorized local route reuse,
  saved-route opt-out, isolated registry lookup, absolute cookie-file pointers,
  and corrected authorization-versus-missing-subtitle diagnosis.
- Public asset policy and defensive ignores for common private local files.

## Deliberately excluded

- Account-specific upload/publishing skills and machine-local credentials/state.
- Unreviewed game-production, animation, font, and board-release additions.
- Broad source/runtime copying: some maintainer files lack the public core's
  newer fixes; line-ending or cache differences are not functional updates.

## Review and verification

Independent Code Auditor and Usability Validator passes identified and repaired
subtitle status precedence, missing browser-login classification, cwd-relative
authorization pointers, contradictory fallback instructions, and an unsupported
documented engine option. Router references were checked for dependency closure.

Reproduce offline checks from the repository root:

```text
python -B scripts/validate-release-skill-gates.py
python -B skills/q-video-intake/scripts/test_public_auth_boundaries.py
python -B skills/q-video-intake/scripts/test_auth_routes.py
python -B skills/q-video-intake/scripts/test_bilibili_page_selection.py
python -B skills/q-workflow/scripts/test_release_v11_regressions.py
python -B skills/q-workflow/scripts/workflow_stability_suite.py --public-install --rounds 2 --strict --fixture-root <temporary-directory> --status-output <private-report.json>
```

Authorization tests use mocked sources and disposable fixtures, not real
credentials. This update does not claim live Bilibili compatibility or visual
approval of an actual artwork/interface merely because its guidance was reviewed.
Generated reports and intake outputs stay outside the public snapshot.
