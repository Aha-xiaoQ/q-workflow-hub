<p align="center">
  <img src="assets/q-logo-pixel-framed.svg" width="96" height="96" alt="Xiao Q pixel logo">
</p>

<h1 align="center">q-workflow</h1>

<p align="center">
  Recover project context from files and Git, not just chat history.
</p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">Simplified Chinese</a>
</p>

<p align="center">
  <a href="QUICKSTART.md">Quickstart</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#documentation">Documentation</a> ·
  <a href="https://github.com/Aha-xiaoQ/q-workflow-hub/issues">Issues</a>
</p>

---

q-workflow is a file- and Git-based workflow layer for coding agents. It keeps
project locations, active tasks, decisions and recovery notes in a private hub
and your project repositories, so a new agent session has a starting point
beyond the conversation.

This repository, **q-workflow-hub**, is the public starter: installers,
templates and reusable skills. Your generated workflow hub stays private.

> **Current package:** [v1.2 scope](docs/releases/q-workflow-v1.2.md) on
> `main`. Setup targets Windows with PowerShell, Git and Python 3.10+.
> This is an early-stage project, not a hosted service or a model.

## Why q-workflow?

Use it when you work across sessions or repositories and need to recover what
was in progress, which files are authoritative, and what has actually been
checked.

- **Resume with context.** A project registry and active-work pointer guide the
  agent to the relevant files.
- **Keep decisions with the work.** Tasks, environment notes and validation
  evidence live alongside the project.
- **Separate reusable skills from private state.** Public templates can be
  shared without publishing your personal workflow hub.
- **Make handoffs traceable.** Local validation and verified publication are
  recorded separately; one does not imply the other.

The workflow is optimized for Codex skills. Other agents that can read and
edit files, run commands and use Git can follow the file-based approach through
[manual bootstrap](MACHINE_BOOTSTRAP.md); equivalent integration is not assumed.

## Get started

**Start with the [English quickstart](QUICKSTART.md).** It contains the
recommended agent-guided setup prompt and the complete prerequisites.

1. Prepare a Windows machine with PowerShell, Git, Python 3.10+ and a
   terminal-capable coding agent.
2. Give the quickstart's setup prompt to your agent. It should explain the
   folders it will create, check the prerequisites and confirm the required
   settings before installing.
3. Keep the generated workflow hub private. Configure provider credentials in
   your agent or secret manager, never in setup prompts.
4. Restart the agent after installation, then try:

```text
Continue my project. Use q-workflow.
```

**Expected result:** the agent finds your configured hub and reports the
current project state. If no project is registered yet, ask it to register an
existing project or create one. See the
[success check](QUICKSTART.md#success-check) and
[after-setup guide](AFTER_SETUP.md) for the next steps.

Setup writes a local profile and managed skill folders. Review the proposed
paths first; use the documented dry run for direct installation. For manual
setup or troubleshooting, stay with the [quickstart](QUICKSTART.md) rather
than copying commands from an older release.

## How it works

The public starter, private hub and project repositories have different jobs:

| Layer | What belongs there |
| --- | --- |
| **Public starter** — this repository | Installers, reusable skills and templates; no personal active-work state. |
| **Private workflow hub** — your local folder | Project registry, active-work pointer, preferences and bootstrap skill copies. An optional private remote provides backup or cross-machine sync. |
| **Project repositories** — your work | Source files, tasks, decisions, environment notes and validation evidence. |

The agent uses the hub to locate a project, then reads that project's files to
resume work. A generated first-run HTML guide explains the setup locally.
See the [boundary model](docs/HUB_BOUNDARY_MODEL.md) before moving material
between layers.

## What's included

The current public package contains **14 reusable skills**:

| Area | Included skills |
| --- | --- |
| Workflow and handoff | `q-workflow`, `q-agent-roster`, `q-code-lifecycle`, `q-skill-creation` |
| Research and source intake | `q-research-discovery`, `q-skill-pattern-learning`, `q-pdf-reading`, `q-video-intake`, `q-audio-intake` |
| Project communication | `q-project-overview`, `q-project-storytelling`, `q-diagram-workflow`, `q-ppt-creation`, `q-ppt-visual-review` |

Setup also generates your customized `q-assistant-profile`. You get setup/update
helpers, project templates and a private-hub template. Start with the
[daily usage guide](AFTER_SETUP.md); you do not need
to learn every skill before using the workflow.

### Scope and limitations

- The current distribution excludes the withdrawn pixel-art, Canvas-game and
  HTML-interface packages. Historical tags are not the current supported
  package; see [v1.2 scope](docs/releases/q-workflow-v1.2.md).
- Validation covers specific workflow and installation behavior. It is not
  evidence of higher model intelligence, creative quality or live-provider
  availability.
- Skills guide agent behavior; they are not a security sandbox or a substitute
  for the agent's own permissions and your review.

## Update an existing installation

Follow [Updating later from GitHub](QUICKSTART.md#updating-later-from-github).
Check the checkout and remote, update the starter, sync the managed copies,
then restart the agent and repeat the resume check.

Do not pull into a dirty or ambiguous checkout. For a detached release checkout,
use the documented migration path. If an old checkout has divergent history,
preserve your local work and clone the current starter into a new directory;
review and reapply your changes instead of merging obsolete history.

The updater does not silently remove withdrawn skills from existing installs.
Preserve custom work before moving those exact folders out of skill discovery.

## Documentation

| I want to… | Read |
| --- | --- |
| Install for the first time | [Quickstart](QUICKSTART.md) |
| Give an agent a first-session brief | [First prompt](FIRST_PROMPT.md) |
| Learn daily usage | [After setup](AFTER_SETUP.md) |
| Use a file-first/manual setup path | [Machine bootstrap](MACHINE_BOOTSTRAP.md) |
| Understand privacy boundaries | [Hub boundary model](docs/HUB_BOUNDARY_MODEL.md) |
| Check the supported package and its tests | [v1.2 scope and verification](docs/releases/q-workflow-v1.2.md) |
| Follow changes | [Changelog](CHANGELOG.md) |

A [Simplified Chinese README](README.zh-CN.md), quickstart, first prompt and
after-setup guide are available. Deeper reference documents may be English-only.

## Contribute and get help

Maintained by [Xiao Q](https://github.com/Aha-xiaoQ). Bug reports,
documentation improvements and reproducible workflow fixes are welcome.
Read the [contribution guide](CONTRIBUTING.md) before opening a pull request.

For general questions or bugs, [open an issue](https://github.com/Aha-xiaoQ/q-workflow-hub/issues).
For security or privacy concerns, follow [SECURITY.md](SECURITY.md).
Never include credentials, private paths or project data in a public report.

## License

[Apache-2.0](LICENSE) for the workflow code and documentation. The current Q
brand artwork has [separate usage terms](assets/README.md). See
[third-party notices](THIRD_PARTY_NOTICES.md) for attribution and references.
