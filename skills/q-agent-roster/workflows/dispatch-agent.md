# Dispatch Agent

Use before spawning or simulating an expert pass.

## Steps

1. Restate the user goal in one sentence.
2. Check `references/agent-registry.md` `Direct Invocation Map` before choosing
   a generic route. If Xiao Q used a specialist phrase, route to the mapped
   stable expert and explain the role choice before execution.
3. Use `references/auto-dispatch-policy.md` to decide whether this is
   local-pass, real platform subagent, ask-before-spawn, or deny.
4. Run the automatic-dispatch check before doing the work:
   - Explicit specialist request: route to the named/mapped expert.
   - Quality-risk review: if the task creates a nontrivial artifact, workflow
     rule, public/team handoff, setup path, code/script change, or repeated
     user-found miss, schedule a read-only reviewer or validator unless a
     smaller local-pass is clearly sufficient.
   - Parallel opportunity: if an independent source scan, install smoke test,
     read-only review, validation command, or disjoint file slice can run while
     the main agent progresses, consider a real subagent with bounded scope.
   - Scenario-class match: check `auto-dispatch-policy.md` for fan-out/fan-in,
     cold-context install/usability, self-review risk, research sidecar,
     sequential phase handoff, guardrail/release review, and validator replay
     before defaulting to main-only execution.
   - Boundary check: verify existing authorization and owned scope. Ask only
     for missing authority or material expansion involving credentials, private
     data, external actions, destructive operations or overlapping writes.
     Authorized public research or owned workspace edits need no repeat question.
5. Decide mode:
   Apply the ordinary-local-check exception in `auto-dispatch-policy.md` when
   delegation is prohibited, unavailable, or lacks useful independent scope.
   Never label a main-agent check independent or use it to pass an explicitly
   independent domain/release gate.
   - Local specialist pass: use when no actual subagent is needed.
   - Subagent-as-tool: use when the main agent should stay in control and only
     needs a bounded result, summary, review, or artifact slice.
   - Phase handoff: use when a specialist should own the next phase before
     returning control, such as build then review then sedimentation.
   - Single subagent: use when Xiao Q explicitly asks for expert/subagent help
     or an independent pass materially improves quality, catches self-review
     risk, or supplies separate evidence.
   - Parallel subagents: use only for disjoint scopes with named owners and
     return contracts.
   Inherit the current model and effort by default and record that decision.
   Read `references/model-routing.md` only when considering an explicit
   override; then record its capacity assessment. Always name expected
   evidence and a stop condition. Do not spawn for model selection alone.
6. Build the context packet from `references/context-guardrails.md`: include
   source-of-truth, current state, owned scope, no-edit zones, constraints, and
   return contract; exclude broad chat history and irrelevant files.
7. Standardize the task objective and output target:
   - objective: user outcome, expert mission, owned scope, out-of-scope,
     acceptance criteria, stop condition, and next owner;
   - output target: chat-only, file report, artifact manifest, or changed files;
   - report location: assigned path or project-local
     `reports/agents/<trace_id>/<expert>-<method>.md` when durable evidence is
     needed.
8. Assign ownership: files, artifact sections, questions, or review gates. For
   parallel work, also assign `agent_slot`, `no_touch_scope`, and an output
   namespace such as `reports/agents/<trace_id>/<agent_slot>/`.
9. Send `AGENT-TASK v2` from `references/handoff-protocol.md`. The task must
   explicitly require `output_format: AGENT-REPORT v1`; for durable or
   nontrivial reviews, include the fixed durable-report section order and the
   expected `report_path`. For a real subagent, include `capacity_decision` and
   require the report to return `capacity_outcome`.
   If a real subagent was already spawned with a prose prompt or incomplete
   packet, immediately send a corrective `AGENT-TASK v2` plus
   `IDENTITY-UPDATE` before waiting for the report. Treat the original prompt
   as a protocol finding, even when the expert's substantive review is useful.
10. Announce the standardized dispatch card from
   `references/auto-dispatch-policy.md` before work starts when possible:
   use a multi-line block with one field per line: `Expert role`, `Run instance`,
   `Mode`, `Mission`, `Permissions`, and `Boundaries`.
   If the platform returns the nickname only after spawn, first use
   `Run instance=<platform type>/pending`, then immediately follow with the final
   `Run instance=<platform type>/<nickname-or-id>` mapping. Do not present the stable
   role and platform nickname as two equivalent names.
11. For real platform subagents, send a short identity update to the subagent
   as soon as the final nickname/id is known. The update must say the stable
   `expert` value and actual `platform_agent` value to use in
   `AGENT-REPORT v1`; the subagent must not report `local-pass` for a real
   run.
12. Continue non-overlapping main-agent work while delegated work runs.
13. Before integration, check the returned report shape. If a real subagent
   returns useful prose without `AGENT-REPORT v1`, `trace_id`, `platform_agent`,
   or next owner, request a corrected report when feasible; otherwise normalize
   the findings in `INTEGRATION v1` and record `packet_complete: fail`.
14. Integrate with `INTEGRATION v1`.
15. Validate the final artifact and record durable lessons when needed.
16. If Xiao Q is expected to review the result, provide the expert review
    summary, integrated fixes, deferred items, validation evidence, and preview
    path before asking for human review.
17. Complete the authorized push, publication or public sync after review and
    validation. Reuse existing scope-specific authorization; ask only if the
    candidate or destination exceeds it or the user revoked it.

## Role Selection Hints

- Use Visual Arbiter (版衡) after visual generation, before handoff.
- Use Source Scout (寻源) before choosing tools, platforms, public examples, or latest facts.
- Use Pagewright (页匠) to build or review HTML-native experiences.
- Use Doc Architect (文构) when the output must become a reusable document or standard.
- Use Code Auditor (码鉴) after code changes or before trusting generated scripts.
- Use Workflow Distiller (沉炼) after repeated misses or major workflow changes.

## Anti-Patterns

- Creating a one-off expert name during dispatch. First map the task to a stable
  role such as `Usability Validator (验用)` or `Doc Architect (文构)`; use
  task labels only in mission/agent_slot, and use platform nicknames only as
  run instances.
- Spawning reviewers with no source artifact.
- Claiming independent review from main-agent self-checks, or skipping an
  explicitly required independent domain/release review because local tests passed.
- Serializing independent source scans, cold install tests, or read-only
  validation work that could have run beside the main path.
- Asking two experts the same broad question.
- Accepting an expert report without checking evidence.
- Accepting a report that omits the agreed `platform_agent`, `report_path`,
  `artifact_manifest`, validation evidence, stop condition result, or next
  owner.
- Treating a structured but non-protocol answer as a standard report. Useful
  prose can be integrated, but the protocol defect must be corrected or logged.
- Sending a real subagent a prose wake-up prompt and relying on the expert to
  infer the standard packet shape. The parent must correct the dispatch, show
  Xiao Q the standard multi-line card, and require `AGENT-REPORT v1` before
  integration when feasible.
- Accepting a real subagent report whose `platform_agent` is `local-pass`,
  `pending`, missing, or otherwise inconsistent with the dispatch card without
  correcting the trace in the integration note.
- Letting two parallel agents write to the same report path, generated artifact,
  or source file without a main-agent serialized handoff.
- Ending with chat-only lessons after a workflow failure.
- Asking Xiao Q to catch basic issues on a nontrivial artifact before the
  mapped expert or subagent has reviewed it.
- Pushing or publishing after self-review only, even when local validation
  passes.
- Passing full conversation context when a smaller context packet would work.
- Giving write-capable ownership to a reviewer that only needs read-only tools.
- Loading every reference file when the task only needs one workflow and one
  protocol.
- Hiding the platform agent identity from Xiao Q, or showing it as an
  ambiguous second name. Without the visible `Expert role` / `Run instance` split, Xiao Q
  cannot judge which expert profile is stable and which handle is only trace
  evidence.
- Treating a direct specialist request as ordinary execution. If Xiao Q asks
  for an installation specialist, tester, reviewer, or named expert, the roster
  route is part of the requested behavior, not optional polish.
