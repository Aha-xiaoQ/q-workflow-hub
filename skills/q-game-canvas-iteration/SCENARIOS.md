# Pilot Scenarios

## Scenario A: Game Feedback Pass

Prompt: "The Fire Flower should stay still after emerging, Fire form should be
visible, and the castle must be the end of the normal level."

Expected route: load this skill and `workflows/iterate-canvas-game.md`.

Pass criteria:

- behavior, draw, HUD/control cue, and reset path are checked for the flower;
- normal map hides bonus-room geometry outside the secret route;
- syntax, state-path, launcher, and package checks are recorded;
- no copyrighted assets or audio are added.

## Scenario B: Legacy Text Alias

Prompt: "Use game-canvas-iteration to improve a local canvas game."

Expected route: the canonical description/metadata recognizes the legacy text
and routes directly to `q-game-canvas-iteration`. No alias skill directory is
installed or loaded.

Pass criteria: the canonical name, workflow, output contract, and validation
path are named in the response, and the old folder is absent.
