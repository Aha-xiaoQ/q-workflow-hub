# Update Skill

Use when improving an existing skill.

For proactive maintenance, first separate the observed signal, the candidate
and permission to activate it using q-workflow's `references/proactive-evolution.md`.
If unavailable, use the same bounded rule: evidence-led, authorized local patch,
negative/transfer checks, prior and accepted revisions, and a revisit condition.
Do not repeat an unchanged review or let this update recursively upgrade itself.

## Steps

1. Run the pre-edit freshness gate for multi-surface or reusable skills: read `references/source-runtime-freshness.md`, list known canonical source/runtime/public/company/personal/user-cache surfaces, check dirty status, compare key files plus scripts, manifests, assets, and default path references, and choose the edit baseline before writing. Do not copy a stale source over a newer runtime or hub, and do not treat a user-local cache as canonical source without an explicit promotion step.
2. Read the chosen baseline `SKILL.md` and the files directly owning the requested behavior. Check `agents/openai.yaml` when triggers/default prompts are affected and relevant work-item/release notes for current constraints. Select references using the entry router, then read each selected instruction completely; do not eagerly load every workflow/reference in the package.
3. Identify whether the change is about triggers, workflow behavior, scripts, references, validation, user experience, compatibility, lifecycle state, or release posture.
4. Classify the update as `patch`, `minor`, or `major` using `references/skill-lifecycle-standard.md`. Use the class to set validation depth, compatibility notes, and whether migration or release review is required.
5. For process, format, recovery, release, or stability rules that will become reusable workflow behavior, run a calibration pass before stabilizing: compare the proposed rule against official documentation, strong adjacent products or public skills, and local failure evidence. Extract mechanisms only; do not copy third-party text, code, prompts, schemas, or assets without license clearance. Record why the rule is a hard gate, procedure, or strong default, then require expert review or a realistic regression scenario before claiming it stable.
6. For high-impact lifecycle, taxonomy, compatibility, release, routing, or policy changes, run the Pre/Post Expert Review Gate in `references/skill-lifecycle-standard.md`: get a pre-review before editing and a post-review before closure. If pre-review was skipped, record the defect and run post-review before final handoff.
7. If the update could expand the skill in different directions, offer an option-style decision before editing. Include a recommended default, impact, files likely to change, compatibility impact, and validation method. Skip this only when the user gave a precise patch request or the correct layer is obvious from files.
8. Keep edits scoped. Preserve existing working behavior unless the user asked to change it or validation shows it is unsafe.
9. Prefer the shortest verified path. When a path has already worked in a real task, make it the default and keep alternatives as fallback or debug paths. Do not add broad process unless it prevents a repeated failure.
10. For behavior rules, use `references/rule-quality.md` and `references/rule-hardness-ladder.md` to choose the trigger, goal, strength, hardness, loading layer, action, anti-pattern, and validation cue. Classify each new or modified rule before writing it as a principle, preference, strong default, procedure, hard gate, or executable gate.
11. For lessons or user corrections, run the Sedimentation Absorption Gate in `references/skill-lifecycle-standard.md` before promoting the lesson into a router, workflow, reference, script, or always-on profile rule.
12. For portfolio fields, use `references/skill-taxonomy-schema.md`; prefer inventory/catalog metadata over unsupported frontmatter.
13. For behavior, trigger, mirror, reusable-rule, or public skill changes, run a related-surface propagation audit. Check source/runtime mirrors, personal bootstrap copies, company/public variants, adjacent skills, `agents/openai.yaml`, workflow docs, scripts, validation gates, and durable handoff notes. Update every applicable surface or record why a surface was intentionally skipped.
14. If the update is driven by a new native agent/platform capability, run a capability replacement audit: use native, wrap native with local gates, keep local, or retire local after a realistic validation scenario. Do not delete a local rule until its old failure mode is covered by observable evidence.
15. Update `agents/openai.yaml` if trigger language or user-facing scope changes.
16. Re-run relevant validation. For behavior or reliability changes, include at least one scenario that exercises the changed path. For hard gates and executable gates, verify the blocked outcome, check method, repair path, waiver rule, and scope before final handoff. For source/runtime mirrors, read back or hash changed key files, run freshness comparison when available, and check that stale nested directories were not left behind. Run encoding guard when localized text, Chinese aliases, expert names, or user-facing markdown changed.
17. For important reusable skills that do not meet the high-impact gate, consider a bounded reviewer or validator pass when it adds concrete evidence. Do not spawn agents for simple text fixes.
18. After a major improvement, repeated execute/feedback/repair loop, new validation method, or user-confirmed satisfactory result, run a consolidation pass and record whether the workflow itself needs a rule, test, or review-gate update.
19. Update durable handoff notes with decisions, change class, compatibility impact, validation, residual risk, sync state, and next actions.

## Review Points

- Did the change make the skill easier to trigger correctly?
- Did it reduce ambiguity or failure risk?
- Did the workflow present meaningful options when multiple directions were plausible?
- Was the update classified as patch, minor, or major, and does validation match that class?
- If the change was high-impact, were pre-review and post-review both run, and if pre-review was skipped, was that recorded as a process defect rather than silently normalized?
- Did the change preserve old prompts or clearly deprecate them?
- Did a lesson or user correction pass the Sedimentation Absorption Gate before being promoted?
- Were all related rule surfaces checked and either updated or intentionally skipped with a reason?
- Did it add unnecessary context to `SKILL.md`?
- Is the rule's trigger, strength, hardness, loading layer, and anti-pattern clear?
- Could the rule become too mechanical or too easy to ignore?
- For any hard gate, is the blocked outcome observable and is the exception path explicit?
- Did it introduce new third-party material or license obligations?
- Did it capture a reusable lesson without leaking project or personal facts?
- Did a final consolidation pass catch lessons that were broader than the immediate artifact or bug fix?
