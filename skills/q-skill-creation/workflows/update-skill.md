# Update Skill

Classify by semantic effect, not diff size. Preserve existing authorization and
unrelated edits; a local update does not authorize publication.

## Common path

1. Read the owning entry and affected rule/consumer. Compare touched files with
   known source/runtime/bootstrap copies; choose the validated baseline before
   writing. Load `../references/source-runtime-freshness.md` only for drift,
   unclear ownership, a new surface or release risk.
2. Choose the lane below. Briefly record what stays, changes or retires and why
   in the existing work item/diff. Do not create another inventory for one file.
3. Edit canonical source. Follow the changed route into consumers, templates and
   UI prompts only where they could restore the old behavior.
4. Validate the claim, propagate touched files, verify hashes, and record one
   compact result. Reuse passed checks until inputs or a new concern invalidate
   them. Stop after the authorized delivery.

| Lane | Applies to | Checks |
|---|---|---|
| Editorial / patch | Wording, links, metadata with unchanged behavior | Readback/diff, affected links, parsing/encoding |
| Behavior / minor | New or adjusted compatible procedure/fallback | Above plus intended path and contrasting/failure case; affected scripts if any |
| High-impact / major | Core routing/authority/output contract, hard gate, compatibility, lifecycle, retirement, broad propagation or release | Independent pre/post review and affected consumer checks; applicable lifecycle/domain/release contract |

Moving text is behavioral when activation or required evidence changes. A simple
behavior rule needs trigger, action, done/failure condition and scenario, not a
large rule form. Load `../references/rule-quality.md` or
`../references/rule-hardness-ladder.md` when designing a gate or resolving its
strength. Load `../references/skill-lifecycle-standard.md` for lifecycle,
compatibility or stable/team/portable claims. Research only unknown/current facts.

For a narrowed check, demonstrate that its protected risk still takes the
stronger route. Byte/line reductions show loading size, not measured speed or
model reliability. Do not claim smaller-model compatibility without actual
target-model evidence. Full installation tests are for changed installation or
rebuild claims; broad stability tests are for the applicable foundation/release
contract, not every prose edit or Git push.
