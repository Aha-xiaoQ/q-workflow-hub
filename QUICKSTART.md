# Quickstart

> **Public beta:** this guide currently targets `v1.1-beta`. For a reproducible
> install, clone the tag with `git clone --branch v1.1-beta --depth 1 ...`.
> Read the [beta limitations and rollback notes](docs/releases/q-workflow-v1.1-beta.md)
> before installing.

Use this guide when you want a coding agent to install q-workflow on a Windows
machine. The recommended path is agent-first: give the agent the public starter
URL and let it run the checks, ask for the few missing fields, install, and
verify.

## Before You Begin

You need:

| Need | Recommended check | Notes |
|:---|:---|:---|
| Git | `git --version` | Required to clone and manage project history. |
| Python 3.10+ | `python --version` | Required for validation and updates. Ensure `python` resolves to the installed interpreter, not the Microsoft Store alias. |
| One coding agent | `codex --version`, open Codex, or `claude --version` | Codex CLI/app or Claude Code are typical choices. |
| PowerShell | Open PowerShell or Windows Terminal | Setup scripts use PowerShell. |
| Writable workspace | `%USERPROFILE%\AI_Work` | Use a normal user folder, not a protected system folder. |
| API key setup | Agent settings, CC Switch, or your secret manager | Do not paste API keys into q-workflow prompts. |

Optional: CC Switch can help manage providers, models, proxies, API keys, MCP,
skills, and prompts from a GUI.

Recommended default paths:

```text
Workspace root: %USERPROFILE%\AI_Work
Workflow hub: %USERPROFILE%\AI_Work\workflow-hub
```

## What q-workflow Will Create

q-workflow adds a small recovery layer around your agent work:

- one private workflow hub with your project registry, active-work pointer,
  assistant profile, first-run guide, and bootstrap skill mirror;
- reusable skills installed into the selected Codex home when you choose runtime
  installation;
- optional Git initialization for the private workflow hub;
- project templates for future recoverable repositories.

Keep the generated workflow hub private. It may contain local paths, project
names, work items, and preferences. If you want backup or cross-machine sync,
use one private Git remote for this workflow hub.

## Recommended Setup

Paste this into Codex, Claude Code, or another terminal-capable coding agent:

```text
Set up q-workflow from this public starter:
https://github.com/Aha-xiaoQ/q-workflow-hub.git

Please guide me step by step in plain language.
Clone and use the immutable `v1.1-beta` tag, not an unpinned default branch.
Use QUICKSTART.md and MACHINE_BOOTSTRAP.md as your setup source.
First explain what q-workflow will create and what should stay private.
Check that Git and my chosen coding agent are installed.
Ask only for the setup fields you need.
Install q-workflow with English generated setup/profile files (`-Language en`
when using the script directly).
After setup, show me the first-run guide, verify it worked, show me the daily
resume prompt, and walk me through the first Quick Resume smoke test.
```

The agent should ask for:

- display name;
- workspace root;
- private workflow hub path;
- optional workflow label for the visible resume marker;
- optional private Git remote for the workflow hub.

## Alternative Setup Paths

Most users can stop at the recommended prompt above. Use these only when the
agent asks for commands, you are testing the package, or you prefer a manual
terminal path.

Guided local runner:

```powershell
git clone --branch v1.1-beta --depth 1 https://github.com/Aha-xiaoQ/q-workflow-hub.git
cd q-workflow-hub
powershell -ExecutionPolicy Bypass -File .\scripts\setup-runner.ps1
```

The runner opens a temporary local page, supports folder selection, and can run
the install script directly. Close the PowerShell window to stop it. It listens
on `127.0.0.1` only and is intended for local setup.

Headless or CI-style direct installer:

```powershell
# Preview all resolved paths first; this writes nothing.
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 `
  -UserName "<display name>" `
  -WorkspaceRoot "$env:USERPROFILE\AI_Work" `
  -WorkflowHubPath "$env:USERPROFILE\AI_Work\workflow-hub" `
  -CodexHome "$env:USERPROFILE\.codex" `
  -WorkflowLabel "q-workflow" `
  -Language "en" `
  -InitializeGit `
  -DryRun

# After reviewing the preview, run the same command without -DryRun.
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 `
  -UserName "<display name>" `
  -WorkspaceRoot "$env:USERPROFILE\AI_Work" `
  -WorkflowHubPath "$env:USERPROFILE\AI_Work\workflow-hub" `
  -CodexHome "$env:USERPROFILE\.codex" `
  -WorkflowLabel "q-workflow" `
  -Language "en" `
  -InitializeGit
```

The direct installer writes `q-profile.json` and replaces the managed `q-*`
skill folders at the selected Codex home. Keep unrelated/private work outside
those managed folders and review the DryRun paths before continuing.

Static intake fallback: open [setup-intake.html](setup-intake.html). Static mode
cannot access full filesystem paths automatically, but it can prepare the setup
request for an agent.

## Updating Later From GitHub

For a branch checkout, update the public starter first, then sync its skills
into your private workflow hub and runtime copy:

```powershell
# Run inside your local q-workflow-hub starter checkout.
git status --short --branch
git remote -v
git pull --ff-only

powershell -ExecutionPolicy Bypass -File .\scripts\sync-workflow-bootstrap.ps1 `
  -WorkflowHubPath "$env:USERPROFILE\AI_Work\workflow-hub" `
  -CodexHome "$env:USERPROFILE\.codex" `
  -InstallRuntime
```

Restart the agent and run the Quick Resume smoke test again. If the checkout is
dirty, the remote is unexpected, or the agent finds multiple starter checkouts,
stop and ask it to report the ambiguity instead of using remote as a blind
overwrite source.

For an immutable beta-tag checkout, do not use `git pull`:

```powershell
git status --short --branch
git remote -v
git fetch --tags origin
git switch --detach v1.1-beta

powershell -ExecutionPolicy Bypass -File .\scripts\sync-workflow-bootstrap.ps1 `
  -WorkflowHubPath "$env:USERPROFILE\AI_Work\workflow-hub" `
  -CodexHome "$env:USERPROFILE\.codex" `
  -InstallRuntime
```

Replace `v1.1-beta` only when a newer reviewed tag is published.

## Success Check

Ask the agent:

```text
Verify that q-workflow was installed correctly and show me the resume prompt.
```

A healthy setup should have:

- a private workflow hub folder;
- `PROJECT_REGISTRY.md`;
- `personal-state\ACTIVE_WORK.md`;
- `FIRST_RUN_GUIDE.html` or `FIRST_RUN_GUIDE.zh-CN.html`;
- `bootstrap\skills` in the workflow hub;
- `bootstrap\skills\q-agent-roster` in the workflow hub;
- `skills\q-workflow` under the selected Codex home when runtime install was
  not skipped;
- `skills\q-agent-roster` under the selected Codex home when runtime install
  was not skipped;
- `skills\q-assistant-profile\SKILL.md` with the expected Quick Resume marker.

The current chat usually will not reload newly installed skills automatically.
For the real new-user test, restart the agent or open a new agent session, then
try:

```text
Continue my project. Use q-workflow.
```

If there is no active project yet, that is normal. Ask the agent to register an
existing project or create a new q-workflow project.

## First Visible Result

After setup, ask:

```text
Open or summarize my FIRST_RUN_GUIDE.html, then register one existing project or
create a small demo q-workflow project.
```

This proves the agent can find your private workflow hub, explain the workflow, and write
recoverable project state instead of only answering in chat.

## Troubleshooting

| Symptom | What to do |
|:---|:---|
| `git` is not recognized | Install Git for Windows, then open a new terminal. |
| `codex` or `claude` is not recognized | Install the agent you want, then open a new terminal. |
| Agent asks for an API key | Configure it in the agent, CC Switch, or your secret manager. Do not paste it into q-workflow prompts. |
| GitHub or another remote times out | Ask the agent to check network access or configure a Git proxy for your environment. |
| Workspace is not writable | Choose a normal user folder such as `%USERPROFILE%\AI_Work`. |
| PowerShell blocks scripts | Run with `powershell -ExecutionPolicy Bypass -File .\scripts\init-user.ps1`. |
| New skills are not recognized | Restart the agent and try the resume prompt again. |
| You want a clean retest | Use a fresh test root such as `$env:USERPROFILE\q-workflow-install-lab\test-<timestamp>`, then clean only that test root. |

## Next Step

For general bugs or feedback, use the
[issue tracker](https://github.com/Aha-xiaoQ/q-workflow-hub/issues). For a
security or privacy problem, follow [SECURITY.md](SECURITY.md) and never put
secrets or private paths in a public issue.

After installation, read [AFTER_SETUP.md](AFTER_SETUP.md). It shows the daily
mental model, useful prompts, and how the assistant should surface helpful
workflow features without making you remember every command.
