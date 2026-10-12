# Phase B Output Preflight

Read before the first Phase B output and again only if the output contract or
managed latch changes. Keep this instruction available through the task.

Before sending every Phase B progress, validation, blocker, or handoff update,
run the smallest output preflight: its first non-empty line MUST be
`小Q工作流 / <registered q-skill-id> / <Chinese current action>`. This applies
to commentary and final handoffs alike; a tool call, validation result, or
subagent result does not waive it. Use
`scripts/phase_b_output_preflight.py --self-test` to validate the grammar
implementation and use its text-file mode for replay fixtures. This preflight
does not require a next-options menu when no meaningful choice remains.

Visible workflow state has a continuity latch. Once an active material task
enters Phase B, every later user-visible assistant message on that task must
keep the slash status line, including short answers, apologies, explanations,
and tool-free follow-ups. The latch ends only when the task is explicitly
closed, paused, switched, or returned to Phase A. A new user correction does
not reset it. Omitting the line is a workflow-state-loss defect: restore it on
the next response and verify the durable pointer before more execution.

The latch is executable state, not prose only. Managed pointers must expose
`visibility_latch: phase-b-required` for `active`, `validating`, or `blocked`
tasks and `visibility_latch: not-required` otherwise. Status, task listing, and
base audit fail closed when the field is missing or contradicts `work_state`.
For output-grammar repair or an explicit protocol-validation claim, run
`phase_b_output_preflight.py --text-file <reply> --active-work <matching pointer>`.
Do not use another task's global focus as this task's identity evidence.

Check ordinary progress prefixes directly; do not launch a process for each
message. Use the text-file validator when repairing or certifying
the output grammar; normal handoffs need a direct prefix check. Required task-event transitions remain unchanged.
