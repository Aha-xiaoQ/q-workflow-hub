# Q-OUTPUT

Use natural concise prose. Include the outcome, useful artifact links, relevant
verification and material gaps; add next steps only when something remains.
Cards are optional readability aids, except exact machine-command output.

## Required status identity

While the managed Phase B latch applies, the first non-empty line is:

```text
小Q工作流 / <skill-id> / <current-action>
```

Use the actual registered skill, not an expert, script, nickname or status.
State belongs on the next line. The owning `q-workflow` Phase B contract governs
the latch, including short answers. Raw internal agent packets retain their
own headers; user-visible summaries keep the status prefix.

## Handoffs

- Completion: actual result, affected artifacts, checks and unresolved gap.
- Blocker: evidence, affected action and the smallest missing input/action.
- Recovery: task/authority, completed vs pending, protected scope and next action.
- Publication: destination, current authorization, verified deployment/release
  state and material risk. Reuse approval already given for that scope.

Do not require English card labels, repeated names, formal status enums, a
next-options menu or a confirmation line when ordinary prose is clear. Preserve
exact `surface.chat_text` for the foundational micro commands.

`**Recommended Next**` is optional for a real unresolved choice or explicit menu
request. `--handoff-output` checks the status line; adding
`--require-next-options` tests the chosen menu form. Do not require that flag
to force a menu into a completed task.
Without a choice, end after the result. Distinguish an untested claim from a
completed task for which no additional test was necessary.

Before delegation, announce role and scope under `../workflows/dispatch-agent.md`.
Formal machine packets use `handoff-protocol.md` only when a consumer needs them.
