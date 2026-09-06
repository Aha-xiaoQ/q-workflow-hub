# Hub Boundary Model

Most users only need one private workflow hub repo.

The public `q-workflow-hub` starter is the installer/source package. Your
private workflow hub is the daily state repo or folder that stores project
routing and recovery state. Project repositories keep project-specific source
and durable memory.

Company/internal, personal, or multi-profile deployments are advanced
maintainer variants. Do not make new users choose between personal and company
endpoints during normal setup.

## 1. Private Workflow Hub

Purpose:

- store the user's active work pointer, project registry, TODOs, journal, and
  generated assistant profile;
- restore the user's workflow state across machines;
- keep local paths and preferences private.

Rules:

- Most users use one private Git remote for this hub when they want backup or
  cross-machine sync.
- May contain local paths and private workflow state.
- Should not become a public product package.
- Pull/update must use the Repository Locator Gate before Git operations.
- Runtime `.codex/q-profile.json` should point to this hub as `hub` and include
  `repositories` for known project/starter repos.

## 2. Public Starter Hub

Purpose:

- provide reusable installer scripts, templates, docs, starter skills, and
  onboarding material;
- generate a new user's private workflow hub;
- stay shareable within its intended audience.

Rules:

- Must not store active state, private project facts, credentials, or
  machine-only recovery pointers.
- Should include `scripts/resolve-workflow-repo.ps1` and
  `scripts/repo-locator-smoke.ps1` so generated hubs can recover repo locations.
- Installer may write the generated user's `q-profile.json`, but the starter
  itself is not the user's active workflow state.
- Readiness requires public safety checks, install smoke tests, and repo-locator
  smoke tests before promotion or push.

## 3. Project Repositories

Purpose:

- store project-specific source, tasks, decisions, validation evidence, and
  continuation prompts;
- avoid bloating the workflow hub with project artifacts.

Rules:

- Project facts belong in the project repo.
- Workflow hub stores only routing and active pointers.
- Starter hub stores templates and reusable workflow logic.

## Locator Boundary

The Repository Locator Gate crosses these roles safely:

1. Workflow hub/runtime profile gives candidate mappings.
2. Starter hub provides the reusable resolver and installer behavior.
3. Project repo identity is accepted only after `.git` and remote match.

A resolver success means "this path is the intended Git repo". It does not mean
"this repo is safe to publish" or "this private workflow state belongs in the
starter".
