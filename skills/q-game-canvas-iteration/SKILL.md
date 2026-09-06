---
name: q-game-canvas-iteration
description: Iterate original browser, Canvas, WebGL, or local desktop-wrapper games. Use when tuning controls, power-ups, enemies, level flow, game feedback, synthesized audio, score/finish sequences, or runnable game validation, including older requests that name game-canvas-iteration.
---

# Q Game Canvas Iteration

Use this q-workflow skill for original local game iteration after concrete
playtest feedback. It converts player observations into scoped code changes,
evidence, and a runnable local package.

## Trigger Router

| User intent | Load |
| --- | --- |
| Several gameplay fixes or a feedback pass | `workflows/iterate-canvas-game.md` |
| Need reusable lessons or regression checks | `references/experience-ledger.md` |
| Need source/runtime, taxonomy, lifecycle, or alias details | `SKILL_METADATA.yaml`, `SOURCE_RUNTIME.md`, `MIGRATION.md` |

## Default Rules

- A gameplay state must have matching behavior, visible feedback, and a
  discoverable control or HUD cue.
- Model power-ups and timers as explicit state transitions, including reset and
  final-seconds warning behavior.
- Test reachable rewards, directional projectiles/enemies, secret-route entry
  and return, and the sequence `score -> celebration -> results`.
- Use original code, art, music, and names. Genre mechanics may inspire design;
  copied third-party assets, code, or audio are out of scope.
- If local-file browser preview is blocked, do not bypass policy. Run syntax,
  static state checks, launcher validation, and record the visual-test gap.

## Outputs

- Scoped changed game files and an updated local package when requested.
- Validation evidence: syntax/state checks, launcher result, and visual test or
  explicit reason it could not run.
- A concise handoff listing controls, changed mechanics, package path, and
  remaining risk.

## References

- `workflows/iterate-canvas-game.md`
- `references/experience-ledger.md`
