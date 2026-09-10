# First Prompt For A Coding Agent

**English** · [Simplified Chinese](FIRST_PROMPT.zh-CN.md)

Paste this into Codex, Claude Code, or another terminal-capable coding agent:

```text
Set up q-workflow from this public starter:
https://github.com/Aha-xiaoQ/q-workflow-hub.git

Please guide me step by step in plain language.
Use QUICKSTART.md and MACHINE_BOOTSTRAP.md as your setup source.
First explain what q-workflow will create and what should stay private.
Check that Git and my chosen coding agent are installed.
Ask only for the setup fields you need, then install q-workflow with English
generated setup/profile files (`-Language en` when using the script directly).
After setup, show me the first-run guide (`FIRST_RUN_GUIDE.html`), verify it
worked, show me the daily resume prompt, and walk me through the first Quick
Resume smoke test.
```

The agent should ask for:

- display name;
- workspace root;
- private workflow hub path;
- optional workflow label for the visible resume marker;
- optional private Git remote for the workflow hub.

After setup, use:

```text
Continue my project. Use q-workflow.
```

Quick Resume smoke test after restarting the agent:

```text
<display name>
```

Expected first marker:

```text
【q-workflow | Quick Resume】
```

To resume a specific project:

```text
Continue <project name>. Use q-workflow.
```

You can also use your display name or project name to help the agent locate work:

```text
Continue <display name or project name>. Use q-workflow.
```
