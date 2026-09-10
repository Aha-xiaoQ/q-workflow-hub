# Skill maintenance — 2026-09-06

**English** | [Simplified Chinese](maintenance-2026-09-06.zh-CN.md)

For the current package, see the [v1.2 release notes](q-workflow-v1.2.md).

## Video intake changes

- Select multipart video pages explicitly.
- Reuse authorized local subtitle routes, with a saved-route opt-out.
- Resolve route registries independently of the current working directory.
- Distinguish browser-login failures from unavailable subtitles.
- Require absolute authorization-file paths.

## Contributor checks

Run from the repository root:

```text
python -B skills/q-video-intake/scripts/test_public_auth_boundaries.py
python -B skills/q-video-intake/scripts/test_auth_routes.py
python -B skills/q-video-intake/scripts/test_bilibili_page_selection.py
python -B skills/q-workflow/scripts/test_release_v11_regressions.py
```

These authorization tests use mocked sources and disposable fixtures, not real
credentials. Keep account credentials and generated reports out of public issues.
