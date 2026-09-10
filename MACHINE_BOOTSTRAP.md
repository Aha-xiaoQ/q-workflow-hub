# Machine Bootstrap

**English** · [Simplified Chinese](MACHINE_BOOTSTRAP.zh-CN.md)

Use this when setting up q-workflow on a new machine. The bootstrap flow is
written for Codex but can be followed by any coding agent that can read files,
write files, run shell commands, and use Git.

## Goal

Create one private workflow hub, install the bundled `q-workflow` and generated
`q-assistant-profile` skills, then resume from that hub.

Default user experience: the user gives the agent the GitHub starter URL, and
the agent guides setup in plain language. Do not make the user choose between
`setup-runner.ps1` and `init-user.ps1` unless they explicitly want a manual or
headless command path.

## Required Fields

Ask the user for:

- Display name
- Workspace root
- Private workflow hub path
- Preferred generated language. Use `en` for English setup and `zh` for Chinese
  setup.
- Optional private workflow hub Git remote
- Optional workflow label for the visible Quick Resume marker. Use
  `q-workflow` by default; a personal branded setup can use a label such as
  `小Q工作流`.

Recommended Windows defaults:

```text
Workspace root: %USERPROFILE%\AI_Work
Workflow hub: %USERPROFILE%\AI_Work\workflow-hub
```

## User-Facing Overview

After the user provides the required fields and before running commands, give a
concise overview of the workflow:

- q-workflow adds a recovery layer for the user's coding agent.
- The public starter contains reusable setup files. It should stay generic and
  public-safe.
- The user's private workflow hub stores project routing, active work, and
  the generated assistant profile. It should stay private. Most users only need
  one private remote repo for this hub.
- Each project repository stores its own code, facts, tasks, decisions,
  environment notes, and continuation prompt.
- Daily resume prompt: `Continue my project. Use q-workflow.` In Chinese,
  `继续我的项目，使用 q-workflow。` is also fine.
- The user manages the agent through project folders, permissions, context,
  durable memory, and reusable skills or automations.
- Current chat context is temporary. Durable files and Git are the recovery
  layer for project facts, decisions, tasks, environment notes, and next steps.
- Tools and MCP servers should be added deliberately, with credentials kept out
  of prompts and project files.
- Private data, credentials, and project artifacts should not be stored in the
  public starter repository.

Avoid unnecessary jargon in the first explanation. If you mention terms such as
`workflow hub`, `CodexHome`, `bootstrap skills`, or `Quick Resume`, explain
them briefly in user language and say why the user should care.

## Bootstrap Commands

If the starter is not cloned yet:

```powershell
git clone https://github.com/Aha-xiaoQ/q-workflow-hub.git
cd q-workflow-hub
```

For an interactive setup where the agent can ask the user for fields, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 -Language "en" -InitializeGit
```

For a headless agent run, remote terminal, or smoke test, provide values
directly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 `
  -UserName "<display name>" `
  -WorkspaceRoot "<workspace root>" `
  -WorkflowHubPath "<workflow hub path>" `
  -CodexHome "<codex home>" `
  -WorkflowLabel "q-workflow" `
  -Language "en" `
  -WorkflowHubRemote "<private workflow hub git remote>" `
  -InitializeGit
```

If there is no private workflow hub remote yet, omit `-WorkflowHubRemote`.

## File-Level Checks

After setup, verify:

- the private workflow hub exists and contains `PROJECT_REGISTRY.md` and
  `personal-state\ACTIVE_WORK.md`;
- for English setup, the private workflow folder contains
  `FIRST_RUN_GUIDE.html`;
- for Chinese setup, the private workflow folder contains
  `FIRST_RUN_GUIDE.zh-CN.html`;
- the private workflow folder contains `bootstrap\skills`;
- the private workflow folder contains `bootstrap\skills\q-agent-roster`;
- the selected Codex home contains `skills\q-workflow`, unless runtime
  skill installation was intentionally skipped;
- the selected Codex home contains `skills\q-agent-roster`, unless runtime
  skill installation was intentionally skipped;
- `skills\q-assistant-profile\SKILL.md` contains the expected Quick Resume
  marker.

Restart Codex after the first install if the new skills are not discovered in
the current session. The existing chat can prove file-level installation, but
it is not a reliable proof of first-user skill loading because it may already
have loaded older skills. For other agents, point them directly at the
generated workflow hub and `skills\q-workflow\SKILL.md`.

For repeatable closed-loop install tests, use an isolated timestamped root and
set all three paths under it: `WorkspaceRoot`, `WorkflowHubPath`, and
`CodexHome`. Do not use the tester's real `%USERPROFILE%\.codex` unless the
goal is to update that real runtime. After validation, remove only the isolated
test root so the next test starts from a clean first-install state.

After restart, run a lightweight smoke test by saying only the display name or
configured workflow nickname. The generated `q-assistant-profile` should answer
with a visible recovery marker such as:

```text
【q-workflow | Quick Resume】
```

If the user chose `-WorkflowLabel "小Q工作流"` with `-Language "zh"`, the marker should become:

```text
【小Q工作流 | 快速恢复】
```

For the daily usage explanation after installation, point the user to
`AFTER_SETUP.md` or `AFTER_SETUP.zh-CN.md`. For visual onboarding, open the
generated first-run guide in the workflow hub.

## Resume

After bootstrap, read:

1. `<workflow hub>\personal-state\ACTIVE_WORK.md`
2. `<workflow hub>\PROJECT_REGISTRY.md`
3. Any active work item named by `ACTIVE_WORK.md`

If no active work item exists, present the project registry and ask the user
which project to work on.

The user may also say `Continue <project name>. Use q-workflow.` or
`继续 <用户名称或项目名称>，使用 q-workflow。`; use the name as routing evidence
against the assistant profile, project registry, and active work state.

## Common Follow-Up Prompts

Register an existing project:

```text
Use q-workflow for this project: <local path or Git URL>.
Register it in my workflow hub and make it resumable.
```

Create a new project:

```text
Create a new q-workflow project named <project name>.
Use <local path> and initialize durable memory files.
```
