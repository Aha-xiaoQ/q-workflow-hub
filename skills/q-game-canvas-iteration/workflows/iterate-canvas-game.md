# Iterate A Canvas Game

## Intake

Convert direct playtest feedback into acceptance criteria. Classify each item:

- input, animation, or control discoverability;
- player, enemy, projectile, or power-up state;
- level reachability, secret route, or camera flow;
- visual/audio feedback;
- score, finish sequence, packaging, or launcher behavior.

Do not replace observed problems with generic polish tasks.

## Implementation Sequence

1. Stabilize the state model: transition, direction, collision, timer, reset,
   persistence.
2. Make each state legible in canvas rendering, HUD, particles, and audio.
3. Repair level geometry and verify normal movement reaches every reward.
4. Finish with score calculation, celebration, and result overlay sequencing.
5. Update controls in the in-game surface or README when mappings change.

## Required Checks

- A small -> big -> fire chain has distinct item art, collection behavior,
  player render state, control, and projectile behavior.
- A timed invincibility state has active, warning, expiry, and reset paths.
- A second turtle-shell interaction uses player-facing direction for launch.
- A secret pipe has an entry, reward room, exit pipe, legal return camera, and
  no visible bonus area after the normal level finish.
- Synthesized music has rests, stays quieter than effects, and obeys mute/pause.
- A completion overlay appears only after the final score and celebration.

## Validation And Handoff

1. Run the language syntax check.
2. Verify each requested mechanic has update, draw, and reset paths.
3. Run the local launcher in dry-run mode.
4. Run a visual playtest when permitted; otherwise state the blocked reason.
5. Package a newly named local build and report its contents.

