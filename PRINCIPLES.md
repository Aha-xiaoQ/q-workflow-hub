# q-workflow Principles

**English** · [Simplified Chinese](PRINCIPLES.zh-CN.md)

q-workflow exists to make agent-assisted project work reliable, friendly, and
easy to resume. The workflow should improve through real use, but reliability
comes first.

## Product Principles

- **Reliability first.** Important state must live in files and Git, not only in
  chat history. A short resume prompt should recover the latest concrete work.
- **User-friendly by default.** Assume users may not know command-line details.
  Use clear checkpoints, plain-language errors, and concrete next actions.
- **Simple and efficient.** Prefer the smallest workflow that preserves safety,
  recovery, and validation. Avoid ceremony that does not improve outcomes.
- **Polished, not bloated.** Successful lessons should become reusable, but not
  everything belongs in the main path. Keep first contact clean, obvious, and
  confidence-building; move advanced details behind clear workflows,
  references, or optional scripts.
- **Continuously improving.** Treat mistakes and friction as product feedback.
  Update durable rules, templates, and skills after meaningful lessons.
- **Learn broadly, implement independently.** Study strong public workflows and
  skills, but respect licenses and keep q-workflow generic.
- **Make quality visible.** Record assumptions, validation gaps, and sync status
  so another agent or maintainer can continue without guessing.

## Skill Principles

- A skill should solve a recurring workflow, not merely collect notes.
- Keep `SKILL.md` concise; move detailed modes into `workflows/` and reusable
  policy into `references/`.
- Keep the default path small. Add optional workflows only when they reduce
  real repeated friction, and avoid making users read advanced machinery before
  they can understand the value.
- Ask option-style questions for high-impact product choices, with a recommended
  default and a clear tradeoff.
- Use scripts for deterministic, repeatable, or failure-prone operations.
- Validate with at least one realistic scenario before calling a skill ready.
- Record third-party references and license posture before publishing.

## Public Safety

The public starter must not contain personal active work, private project data,
credentials, or machine-specific artifacts. Personal preferences and private
routing state belong in the user's private workflow hub.
